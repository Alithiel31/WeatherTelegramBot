import os
import httpx
import logging
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardRemove
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
    ConversationHandler,
)

# 1. Configuration des logs
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

# 2. Chargement des secrets depuis le fichier .env
load_dotenv()
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

# 3. Définition des états pour la machine à états de la conversation
PAYS, VILLE = range(2)


# --- FONCTION DE RÉCUPÉRATION MÉTÉO ---
async def fetch_weather(city: str, country: str):
    """
    Interroge l'API WeatherAPI de manière asynchrone.
    """
    query = f"{city},{country}"
    url = (
        f"http://api.weatherapi.com/v1/current.json"
        f"?key={WEATHER_API_KEY}&q={query}&lang=fr"
    )

    # On utilise un gestionnaire de contexte 'async with' pour le client HTTP
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
            return message

        except httpx.HTTPError as e:
            logging.error(f"Erreur réseau : {e}")
            return "❌ Impossible de contacter le service météo pour le moment."
        except Exception as e:
            logging.error(f"Erreur inattendue : {e}")
            return "❌ Une erreur technique est survenue."


# --- GESTIONNAIRES DE COMMANDES (HANDLERS) ---


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Démarre la conversation et demande le pays."""
    await update.message.reply_text(
        "🌍 Quel pays vous intéresse ? (Ex: France, Canada...)"
    )
    return PAYS


async def get_country(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Enregistre le pays et demande la ville."""
    context.user_data["country"] = update.message.text
    await update.message.reply_text(
        f"🏙️ Très bien ! Quelle ville de *{update.message.text}*"
        f"voulez-vous consulter ?",
        parse_mode="Markdown",
    )
    return VILLE


async def get_city_and_weather(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Récupère la météo finale et termine la conversation."""
    city = update.message.text
    country = context.user_data.get("country")

    # Affiche "en train d'écrire..." dans Telegram pour l'immersion
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id, action="typing"
    )

    # Appel de notre fonction de météo asynchrone
    weather_info = await fetch_weather(city, country)

    await update.message.reply_text(weather_info, parse_mode="Markdown")
    await update.message.reply_text("Tapez /start pour une nouvelle recherche.")

    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Annule et ferme la conversation."""
    await update.message.reply_text(
        "Recherche annulée. À bientôt !", reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END


# --- LANCEMENT DU BOT ---
if __name__ == "__main__":
    # Vérification de sécurité pour les clés API
    if not TELEGRAM_TOKEN or not WEATHER_API_KEY:
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
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv_handler)

    print("🤖 Le bot météo est prêt à recevoir des messages !")
    app.run_polling()
