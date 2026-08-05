import asyncio
import logging
import unicodedata
from urllib.parse import quote

import httpx
from cachetools import TTLCache

from weather_bot.services import metrics
from weather_bot.config import (
    WEATHER_API_KEY,
    WEATHER_CACHE_TTL,
    WEATHER_CACHE_MAXSIZE,
    FETCH_MAX_RETRIES,
    FETCH_RETRY_BACKOFF_BASE,
    FORECAST_DAYS,
)

CURRENT_URL = "https://api.weatherapi.com/v1/current.json"
FORECAST_URL = "https://api.weatherapi.com/v1/forecast.json"

# Cache mémoire à expiration automatique : {(city, country): message}
_cache: TTLCache = TTLCache(maxsize=WEATHER_CACHE_MAXSIZE, ttl=WEATHER_CACHE_TTL)
_forecast_cache: TTLCache = TTLCache(
    maxsize=WEATHER_CACHE_MAXSIZE, ttl=WEATHER_CACHE_TTL
)


def _cache_key(city: str, country: str) -> tuple[str, str]:
    return (city.lower().strip(), country.lower().strip())


def _strip_accents(text: str) -> str:
    """Retire les diacritiques (accents) d'une chaîne.

    WeatherAPI résout mal les noms de lieux accentués : une recherche pour
    "Montréal" peut renvoyer un lieu incorrect alors que "Montreal" (sans
    accent) fonctionne très bien. On envoie donc toujours une version ASCII
    à l'API, tout en gardant le texte original tel quel pour l'affichage."""
    normalized = unicodedata.normalize("NFKD", text)
    return "".join(c for c in normalized if not unicodedata.combining(c))


def _build_query(city: str, country: str) -> str:
    """Construit le paramètre `q` de WeatherAPI. Le pays est optionnel : sans lui,
    WeatherAPI se contente de résoudre la ville la plus probable."""
    city, country = _strip_accents(city), _strip_accents(country)
    location = f"{city},{country}" if country else city
    return quote(location)


async def _perform_request(url: str) -> tuple[str | None, dict | None]:
    """
    Interroge WeatherAPI de manière asynchrone, avec retry/backoff sur les
    erreurs réseau transitoires. Retourne soit (message_erreur, None) en cas
    d'échec, soit (None, données_json) en cas de succès.
    """
    metrics.increment("requests")
    last_error: Exception | None = None

    for attempt in range(1, FETCH_MAX_RETRIES + 1):
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=10.0)

            # Gestion spécifique d'une erreur de saisie (Code 400)
            if response.status_code == 400:
                metrics.increment("errors")
                return (
                    "⚠️ Lieu non trouvé. "
                    "Vérifiez l'orthographe du pays ou de la ville.",
                    None,
                )

            # Clé API invalide/refusée : pas la peine de retry, ça ne changera pas
            if response.status_code in (401, 403):
                logging.error(
                    f"Clé API WeatherAPI invalide ou refusée "
                    f"(code {response.status_code})"
                )
                metrics.increment("errors")
                return (
                    "❌ Configuration du service météo invalide. "
                    "Contactez l'administrateur.",
                    None,
                )

            # Rate limit atteint côté WeatherAPI : inutile de retry immédiatement
            if response.status_code == 429:
                logging.warning("Rate limit WeatherAPI atteint")
                metrics.increment("errors")
                return (
                    "⏳ Le service météo est temporairement surchargé. "
                    "Réessayez dans quelques instants.",
                    None,
                )

            response.raise_for_status()  # Lève une erreur si statut 4xx/5xx restant
            return None, response.json()

        except ValueError as e:
            # JSON invalide : ce n'est pas transitoire, retry inutile.
            logging.error(f"Réponse WeatherAPI inattendue (JSON invalide) : {e}")
            metrics.increment("errors")
            return "❌ Une erreur technique est survenue.", None

        except httpx.HTTPError as e:
            last_error = e
            logging.warning(
                f"Erreur réseau (tentative {attempt}/{FETCH_MAX_RETRIES}) : {e}"
            )
            if attempt < FETCH_MAX_RETRIES:
                await asyncio.sleep(FETCH_RETRY_BACKOFF_BASE * (2 ** (attempt - 1)))

    logging.error(f"Erreur réseau après {FETCH_MAX_RETRIES} tentatives : {last_error}")
    metrics.increment("errors")
    return "❌ Impossible de contacter le service météo pour le moment.", None


async def fetch_weather(city: str, country: str) -> str:
    """
    Interroge WeatherAPI pour la météo actuelle, avec cache mémoire
    (TTL + taille bornée) et retry/backoff sur les erreurs réseau transitoires.
    """
    key = _cache_key(city, country)
    cached = _cache.get(key)
    if cached is not None:
        logging.info(f"Cache hit pour {city}, {country}")
        metrics.increment("cache_hits")
        return cached

    url = f"{CURRENT_URL}?key={WEATHER_API_KEY}&q={_build_query(city, country)}&lang=fr"

    error, data = await _perform_request(url)
    if error:
        return error

    try:
        assert data is not None
        loc = data["location"]
        cur = data["current"]

        message = (
            f"📍 *{loc['name']}, {loc['country']}*\n"
            f"🌤️ Condition : {cur['condition']['text']}\n"
            f"🌡️ Température : {cur['temp_c']}°C\n"
            f"💧 Humidité : {cur['humidity']}%\n"
            f"💨 Vent : {cur['wind_kph']} km/h"
        )
    except KeyError as e:
        logging.error(f"Réponse WeatherAPI inattendue : {e}")
        metrics.increment("errors")
        return "❌ Une erreur technique est survenue."

    _cache[key] = message
    return message


async def fetch_forecast(city: str, country: str, days: int = FORECAST_DAYS) -> str:
    """
    Interroge WeatherAPI pour une prévision sur plusieurs jours (par défaut
    `FORECAST_DAYS`), avec le même cache/retry que `fetch_weather`.
    """
    key = _cache_key(city, country)
    cached = _forecast_cache.get(key)
    if cached is not None:
        logging.info(f"Cache hit prévision pour {city}, {country}")
        metrics.increment("cache_hits")
        return cached

    url = (
        f"{FORECAST_URL}?key={WEATHER_API_KEY}&q={_build_query(city, country)}"
        f"&days={days}&lang=fr"
    )

    error, data = await _perform_request(url)
    if error:
        return error

    try:
        assert data is not None
        loc = data["location"]
        forecast_days = data["forecast"]["forecastday"]

        lines = [f"📅 *Prévisions pour {loc['name']}, {loc['country']}*"]
        for day in forecast_days:
            d = day["day"]
            lines.append(
                f"\n🗓️ {day['date']}\n"
                f"🌤️ {d['condition']['text']}\n"
                f"🌡️ Min {d['mintemp_c']}°C / Max {d['maxtemp_c']}°C\n"
                f"💧 Humidité moy. : {d['avghumidity']}%\n"
                f"🌧️ Chance de pluie : {d['daily_chance_of_rain']}%"
            )
        message = "\n".join(lines)
    except KeyError as e:
        logging.error(f"Réponse WeatherAPI (prévision) inattendue : {e}")
        metrics.increment("errors")
        return "❌ Une erreur technique est survenue."

    _forecast_cache[key] = message
    return message
