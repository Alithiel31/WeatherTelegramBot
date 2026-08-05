from telegram import Update, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler

from weather_bot.config import PAYS, VILLE, MAX_INPUT_LENGTH
from weather_bot.services import metrics
from weather_bot.services.rate_limiter import is_rate_limited
from weather_bot.services.weather_api import fetch_weather, fetch_forecast


def _is_valid_input(text: str | None) -> bool:
    """Vérifie qu'un texte utilisateur (pays/ville) est non vide et raisonnable."""
    return bool(text) and 1 <= len(text.strip()) <= MAX_INPUT_LENGTH


def _parse_city_country(args_text: str) -> tuple[str, str]:
    """Découpe l'argument brut d'une commande rapide (`/meteo Paris, France`)
    en (ville, pays). Le pays est optionnel."""
    city, _, country = args_text.partition(",")
    return city.strip(), country.strip()


async def _reply_rate_limited(update: Update) -> None:
    metrics.increment("rate_limited")
    await update.message.reply_text(
        "⏳ Trop de requêtes en peu de temps. Merci de patienter un instant "
        "avant de réessayer."
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Démarre la conversation et demande le pays."""
    await update.message.reply_text(
        "🌍 Quel pays vous intéresse ? (Ex: France, Canada...)"
    )
    return PAYS


async def get_country(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Enregistre le pays et demande la ville."""
    text = update.message.text

    if not _is_valid_input(text):
        await update.message.reply_text(
            f"⚠️ Merci d'indiquer un nom de pays valide "
            f"(1 à {MAX_INPUT_LENGTH} caractères)."
        )
        return PAYS

    context.user_data["country"] = text
    await update.message.reply_text(
        f"🏙️ Très bien ! Quelle ville de *{text}* voulez-vous consulter ?",
        parse_mode="Markdown",
    )
    return VILLE


async def get_city_and_weather(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Récupère la météo finale et termine la conversation."""
    city = update.message.text
    country = context.user_data.get("country")
    chat_id = update.effective_chat.id

    if not _is_valid_input(city):
        await update.message.reply_text(
            f"⚠️ Merci d'indiquer un nom de ville valide "
            f"(1 à {MAX_INPUT_LENGTH} caractères)."
        )
        return VILLE

    if is_rate_limited(chat_id):
        await _reply_rate_limited(update)
        return ConversationHandler.END

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


async def meteo_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Commande rapide `/meteo <ville>[, <pays>]` : donne la météo actuelle
    en un seul message, sans passer par le dialogue pas à pas de /start."""
    chat_id = update.effective_chat.id
    args_text = " ".join(context.args) if context.args else ""
    city, country = _parse_city_country(args_text)

    if not _is_valid_input(city) or (country and not _is_valid_input(country)):
        await update.message.reply_text(
            f"⚠️ Utilisation : /meteo <ville>[, <pays>]\n"
            f"Ex : /meteo Paris, France (max {MAX_INPUT_LENGTH} caractères par champ)"
        )
        return

    if is_rate_limited(chat_id):
        await _reply_rate_limited(update)
        return

    await context.bot.send_chat_action(chat_id=chat_id, action="typing")
    weather_info = await fetch_weather(city, country)
    await update.message.reply_text(weather_info, parse_mode="Markdown")


async def prevision_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Commande rapide `/prevision <ville>[, <pays>]` : prévision météo sur
    plusieurs jours (voir `FORECAST_DAYS`)."""
    chat_id = update.effective_chat.id
    args_text = " ".join(context.args) if context.args else ""
    city, country = _parse_city_country(args_text)

    if not _is_valid_input(city) or (country and not _is_valid_input(country)):
        await update.message.reply_text(
            f"⚠️ Utilisation : /prevision <ville>[, <pays>]\n"
            f"Ex : /prevision Paris, France "
            f"(max {MAX_INPUT_LENGTH} caractères par champ)"
        )
        return

    if is_rate_limited(chat_id):
        await _reply_rate_limited(update)
        return

    await context.bot.send_chat_action(chat_id=chat_id, action="typing")
    forecast_info = await fetch_forecast(city, country)
    await update.message.reply_text(forecast_info, parse_mode="Markdown")
