import os
import logging
from dotenv import load_dotenv

# Chargement des secrets depuis le fichier .env
load_dotenv()

WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

# Durée (en secondes) avant qu'une conversation inactive soit fermée automatiquement
CONVERSATION_TIMEOUT = int(os.getenv("CONVERSATION_TIMEOUT", "300"))

# Durée de vie du cache météo (en secondes)
WEATHER_CACHE_TTL = int(os.getenv("WEATHER_CACHE_TTL", "600"))

# États de la machine à états de la conversation
PAYS, VILLE = range(2)


def configure_logging():
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=logging.INFO,
    )


def check_required_config():
    """Vérifie que les secrets obligatoires sont bien présents."""
    return bool(TELEGRAM_TOKEN) and bool(WEATHER_API_KEY)
