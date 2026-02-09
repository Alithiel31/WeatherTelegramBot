import os
import requests
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

# Configuration des logs
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

load_dotenv()

WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

# États de la conversation
PAYS, VILLE = range(2)


def get_weather(city, country):
    # On combine ville et pays pour l'API (ex: "Paris, France")
    query = f"{city},{country}"
    url = f"http://api.weatherapi.com/v1/current.json?key={WEATHER_API_KEY}&q={query}&lang=fr"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        if "location" in data:
            location = f"{data['location']['name']}, {data['location']['country']}"
            condition = data["current"]["condition"]["text"]
            temp = data["current"]["temp_c"]
            humidity = data["current"]["humidity"]
            wind = data["current"]["wind_kph"]
            return f"📍 {location}\n🌤️ {condition}\n🌡️ {temp}°C\n💧 Humidité : {humidity}%\n💨 Vent : {wind} km/h"
        return "⚠️ Lieu non trouvé. Vérifiez l'orthographe."
    except Exception as e:
        logging.error(f"Erreur API : {e}")
        return "❌ Erreur de connexion au service météo."


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🌍 Quel pays vous intéresse ?")
    return PAYS


async def get_country(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["country"] = update.message.text
    await update.message.reply_text(
        f"🏙️ Très bien ! Quelle ville de {update.message.text} voulez-vous consulter ?"
    )
    return VILLE


async def get_city_and_weather(update: Update, context: ContextTypes.DEFAULT_TYPE):
    city = update.message.text
    country = context.user_data.get("country")

    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id, action="typing"
    )

    weather_info = get_weather(city, country)
    await update.message.reply_text(weather_info)
    await update.message.reply_text("Tapez /start pour une nouvelle recherche.")

    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Recherche annulée.", reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END


if __name__ == "__main__":
    if not TELEGRAM_TOKEN or not WEATHER_API_KEY:
        logging.error("❌ Erreur : TOKEN ou API_KEY manquant")
        exit(1)

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    # Mise en place du gestionnaire de conversation
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

    print("🤖 Bot météo par étapes en ligne !")
    app.run_polling()
