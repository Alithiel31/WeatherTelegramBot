import time
import logging
from urllib.parse import quote

import httpx

from config import WEATHER_API_KEY, WEATHER_CACHE_TTL

BASE_URL = "https://api.weatherapi.com/v1/current.json"

# Cache mémoire très simple : {(city, country): (timestamp, message)}
_cache: dict[tuple[str, str], tuple[float, str]] = {}


def _cache_get(city: str, country: str) -> str | None:
    key = (city.lower().strip(), country.lower().strip())
    entry = _cache.get(key)
    if entry is None:
        return None
    timestamp, message = entry
    if time.time() - timestamp > WEATHER_CACHE_TTL:
        del _cache[key]
        return None
    return message


def _cache_set(city: str, country: str, message: str) -> None:
    key = (city.lower().strip(), country.lower().strip())
    _cache[key] = (time.time(), message)


async def fetch_weather(city: str, country: str) -> str:
    """
    Interroge l'API WeatherAPI de manière asynchrone (avec cache mémoire).
    """
    cached = _cache_get(city, country)
    if cached is not None:
        logging.info(f"Cache hit pour {city}, {country}")
        return cached

    # Encodage des paramètres pour éviter les erreurs sur les espaces/accents
    # et toute tentative d'injection dans les paramètres de requête.
    query = quote(f"{city},{country}")
    url = f"{BASE_URL}?key={WEATHER_API_KEY}&q={query}&lang=fr"

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, timeout=10.0)

            # Gestion spécifique d'une erreur de saisie (Code 400)
            if response.status_code == 400:
                return (
                    "⚠️ Lieu non trouvé. Vérifiez l'orthographe du pays ou de la ville."
                )

            response.raise_for_status()  # Lève une erreur si le statut est 4xx ou 5xx
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
            _cache_set(city, country, message)
            return message

        except httpx.HTTPError as e:
            logging.error(f"Erreur réseau : {e}")
            return "❌ Impossible de contacter le service météo pour le moment."
        except Exception as e:
            logging.error(f"Erreur inattendue : {e}")
            return "❌ Une erreur technique est survenue."
