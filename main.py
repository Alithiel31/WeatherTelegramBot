import os
import requests
import logging  # Corrigé : Import ajouté
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# Configuration des logs
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

load_dotenv()

WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

def get_weather(city):
    url = f"http://api.weatherapi.com/v1/current.json?key={WEATHER_API_KEY}&q={city}&lang=fr"
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
        else:
            return "⚠️ Ville non trouvée ou erreur API."

    except requests.exceptions.RequestException as e:
        logging.error(f"Erreur API Météo : {e}")
        return "❌ Désolé, je n'arrive pas à joindre le service météo pour le moment."

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Bienvenue ! Envoie-moi simplement le nom d'une ville pour obtenir la météo ☁️.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    city = update.message.text
    # Indicateur "en train d'écrire"
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    weather_info = get_weather(city)
    await update.message.reply_text(weather_info)

if __name__ == '__main__':
    # Corrigé : Indentation de tout le bloc ci-dessous
    if not TELEGRAM_TOKEN or not WEATHER_API_KEY:
        logging.error("❌ Erreur : TOKEN ou API_KEY manquant dans le .env")
        exit(1)

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🤖 Bot météo en ligne !")
    app.run_polling()