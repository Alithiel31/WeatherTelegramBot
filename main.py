import logging
import time

from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    ConversationHandler,
    PicklePersistence,
    filters,
)

from weather_bot.services import metrics
from weather_bot.config import (
    PAYS,
    VILLE,
    TELEGRAM_TOKEN,
    CONVERSATION_TIMEOUT,
    HEARTBEAT_FILE,
    HEARTBEAT_INTERVAL_SECONDS,
    METRICS_LOG_INTERVAL_SECONDS,
    PERSISTENCE_FILE,
    configure_logging,
    check_required_config,
)
from weather_bot.handlers import (
    start,
    get_country,
    get_city_and_weather,
    cancel,
    timeout,
    meteo_command,
    prevision_command,
)

configure_logging()


async def write_heartbeat(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Écrit un fichier heartbeat régulièrement, utilisé par le HEALTHCHECK Docker
    pour vérifier que le bot répond réellement (et pas juste que le process tourne)."""
    with open(HEARTBEAT_FILE, "w") as f:
        f.write(str(time.time()))


async def log_metrics(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Publie périodiquement les compteurs de métriques dans les logs."""
    logging.info(f"📊 Statistiques : {metrics.snapshot()}")


# --- LANCEMENT DU BOT ---
if __name__ == "__main__":
    # Vérification de sécurité pour les clés API
    if not check_required_config():
        logging.error("❌ Erreur : TOKEN ou API_KEY manquant dans le fichier .env")
        exit(1)

    # Persistance : une conversation en cours (pays déjà saisi, ville en attente)
    # survit à un redémarrage du bot si ce fichier est sur un volume monté
    # (voir docker-compose.yml).
    persistence = PicklePersistence(filepath=PERSISTENCE_FILE)

    # Création de l'application
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).persistence(persistence).build()

    # Configuration du tunnel de conversation
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            PAYS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_country)],
            VILLE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_city_and_weather)
            ],
            ConversationHandler.TIMEOUT: [MessageHandler(filters.ALL, timeout)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        conversation_timeout=CONVERSATION_TIMEOUT,
        name="weather_conversation",
        persistent=True,
    )

    app.add_handler(conv_handler)

    # Commandes rapides indépendantes du dialogue pas à pas (groupe distinct
    # pour qu'elles restent utilisables même si une conversation /start est en
    # cours dans un autre chat/état).
    app.add_handler(CommandHandler("meteo", meteo_command), group=1)
    app.add_handler(CommandHandler("prevision", prevision_command), group=1)

    # Tâches de fond : heartbeat pour le healthcheck Docker + log périodique métriques
    if app.job_queue is not None:
        app.job_queue.run_repeating(
            write_heartbeat, interval=HEARTBEAT_INTERVAL_SECONDS, first=0
        )
        app.job_queue.run_repeating(
            log_metrics,
            interval=METRICS_LOG_INTERVAL_SECONDS,
            first=METRICS_LOG_INTERVAL_SECONDS,
        )
    else:
        logging.warning(
            "JobQueue indisponible (extra 'job-queue' non installé) : "
            "heartbeat et métriques périodiques désactivés."
        )

    print("🤖 Le bot météo est prêt à recevoir des messages !")
    app.run_polling()
