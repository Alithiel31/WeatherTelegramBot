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

# Taille maximale du cache météo (nombre d'entrées ville/pays distinctes)
WEATHER_CACHE_MAXSIZE = int(os.getenv("WEATHER_CACHE_MAXSIZE", "500"))

# Rate limiting : nombre de requêtes météo autorisées par chat sur la fenêtre glissante
RATE_LIMIT_MAX_REQUESTS = int(os.getenv("RATE_LIMIT_MAX_REQUESTS", "5"))
RATE_LIMIT_WINDOW_SECONDS = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60"))

# Longueur maximale acceptée pour les entrées pays/ville
MAX_INPUT_LENGTH = int(os.getenv("MAX_INPUT_LENGTH", "60"))

# Nombre max de tentatives / délai de base (secondes) pour le retry réseau
FETCH_MAX_RETRIES = int(os.getenv("FETCH_MAX_RETRIES", "3"))
FETCH_RETRY_BACKOFF_BASE = float(os.getenv("FETCH_RETRY_BACKOFF_BASE", "0.5"))

# Intervalle (en secondes) entre deux publications des statistiques dans les logs
METRICS_LOG_INTERVAL_SECONDS = int(os.getenv("METRICS_LOG_INTERVAL_SECONDS", "3600"))

# Chemin du fichier heartbeat utilisé par le HEALTHCHECK Docker
HEARTBEAT_FILE = os.getenv("HEARTBEAT_FILE", "/tmp/bot_heartbeat")
HEARTBEAT_INTERVAL_SECONDS = int(os.getenv("HEARTBEAT_INTERVAL_SECONDS", "30"))

# Fichier de persistance des conversations en cours (survit aux redémarrages
# du bot si ce chemin pointe vers un volume monté, cf. docker-compose.yml)
PERSISTENCE_FILE = os.getenv("PERSISTENCE_FILE", "bot_persistence.pickle")

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
