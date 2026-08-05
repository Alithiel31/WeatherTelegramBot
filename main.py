from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    filters,
)

from config import (
    PAYS,
    VILLE,
    TELEGRAM_TOKEN,
    CONVERSATION_TIMEOUT,
    configure_logging,
    check_required_config,
)
from handlers import start, get_country, get_city_and_weather, cancel, timeout

import logging

configure_logging()

# --- LANCEMENT DU BOT ---
if __name__ == "__main__":
    # Vérification de sécurité pour les clés API
    if not check_required_config():
        logging.error("❌ Erreur : TOKEN ou API_KEY manquant dans le fichier .env")
        exit(1)

    # Création de l'application
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

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
    )

    app.add_handler(conv_handler)

    print("🤖 Le bot météo est prêt à recevoir des messages !")
    app.run_polling()
