import asyncio
import logging
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
)

BASE_URL = "https://api.weatherapi.com/v1/current.json"

# Cache mémoire à expiration automatique : {(city, country): message}
_cache: TTLCache = TTLCache(maxsize=WEATHER_CACHE_MAXSIZE, ttl=WEATHER_CACHE_TTL)


def _cache_key(city: str, country: str) -> tuple[str, str]:
    return (city.lower().strip(), country.lower().strip())


async def fetch_weather(city: str, country: str) -> str:
    """
    Interroge l'API WeatherAPI de manière asynchrone, avec cache mémoire
    (TTL + taille bornée) et retry/backoff sur les erreurs réseau transitoires.
    """
    key = _cache_key(city, country)
    cached = _cache.get(key)
    if cached is not None:
        logging.info(f"Cache hit pour {city}, {country}")
        metrics.increment("cache_hits")
        return cached

    # Encodage des paramètres pour éviter les erreurs sur les espaces/accents
    # et toute tentative d'injection dans les paramètres de requête.
    query = quote(f"{city},{country}")
    url = f"{BASE_URL}?key={WEATHER_API_KEY}&q={query}&lang=fr"

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
                    "⚠️ Lieu non trouvé. Vérifiez l'orthographe du pays ou de la ville."
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
                    "Contactez l'administrateur."
                )

            # Rate limit atteint côté WeatherAPI : inutile de retry immédiatement
            if response.status_code == 429:
                logging.warning("Rate limit WeatherAPI atteint")
                metrics.increment("errors")
                return (
                    "⏳ Le service météo est temporairement surchargé. "
                    "Réessayez dans quelques instants."
                )

            response.raise_for_status()  # Lève une erreur si statut 4xx/5xx restant
            data = response.json()

            # Extraction des données JSON
            loc = data["location"]
            cur = data["current"]

            # Construction d'un message clair
            message = (
                f"📍 *{loc['name']}, {loc['country']}*\n"
                f"🌤️ Condition : {cur['condition']['text']}\n"
                f"🌡️ Température : {cur['temp_c']}°C\n"
                f"💧 Humidité : {cur['humidity']}%\n"
                f"💨 Vent : {cur['wind_kph']} km/h"
            )
            _cache[key] = message
            return message

        except (KeyError, ValueError) as e:
            # Schéma de réponse inattendu (champ manquant, JSON invalide) :
            # ce n'est pas transitoire, retry inutile.
            logging.error(f"Réponse WeatherAPI inattendue : {e}")
            metrics.increment("errors")
            return "❌ Une erreur technique est survenue."

        except httpx.HTTPError as e:
            last_error = e
            logging.warning(
                f"Erreur réseau (tentative {attempt}/{FETCH_MAX_RETRIES}) : {e}"
            )
            if attempt < FETCH_MAX_RETRIES:
                await asyncio.sleep(FETCH_RETRY_BACKOFF_BASE * (2 ** (attempt - 1)))

    logging.error(f"Erreur réseau après {FETCH_MAX_RETRIES} tentatives : {last_error}")
    metrics.increment("errors")
    return "❌ Impossible de contacter le service météo pour le moment."
