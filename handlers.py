from telegram import Update, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler

from config import PAYS, VILLE
from weather_api import fetch_weather


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
        f"🏙️ Très bien ! Quelle ville de *{update.message.text}* "
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


async def timeout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ferme la conversation après une période d'inactivité."""
    if update.message:
        await update.message.reply_text(
            "⏱️ Vous n'avez pas répondu à temps, la recherche a été annulée. "
            "Tapez /start pour recommencer.",
            reply_markup=ReplyKeyboardRemove(),
        )
    return ConversationHandler.END
