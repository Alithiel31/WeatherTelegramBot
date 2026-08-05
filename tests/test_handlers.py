import pytest
from telegram.ext import ConversationHandler

from weather_bot.config import PAYS, VILLE, RATE_LIMIT_MAX_REQUESTS
from weather_bot.handlers import (
    start,
    get_country,
    get_city_and_weather,
    cancel,
    timeout,
)
from weather_bot.services.rate_limiter import _requests


@pytest.fixture(autouse=True)
def clear_rate_limiter():
    _requests.clear()
    yield
    _requests.clear()


def make_update(mocker, text=None, chat_id=123):
    update = mocker.Mock()
    update.message = mocker.Mock()
    update.message.text = text
    update.message.reply_text = mocker.AsyncMock()
    update.effective_chat = mocker.Mock()
    update.effective_chat.id = chat_id
    return update


def make_context(mocker, user_data=None):
    context = mocker.Mock()
    context.user_data = user_data if user_data is not None else {}
    context.bot = mocker.Mock()
    context.bot.send_chat_action = mocker.AsyncMock()
    return context


@pytest.mark.asyncio
async def test_start_asks_for_country(mocker):
    update = make_update(mocker)
    context = make_context(mocker)

    state = await start(update, context)

    update.message.reply_text.assert_awaited_once()
    assert "pays" in update.message.reply_text.call_args.args[0].lower()
    assert state == PAYS


@pytest.mark.asyncio
async def test_get_country_stores_country_and_asks_for_city(mocker):
    update = make_update(mocker, text="France")
    context = make_context(mocker)

    state = await get_country(update, context)

    assert context.user_data["country"] == "France"
    update.message.reply_text.assert_awaited_once()
    assert state == VILLE


@pytest.mark.asyncio
async def test_get_country_rejects_empty_input(mocker):
    update = make_update(mocker, text="   ")
    context = make_context(mocker)

    state = await get_country(update, context)

    assert "country" not in context.user_data
    assert state == PAYS


@pytest.mark.asyncio
async def test_get_country_rejects_too_long_input(mocker):
    update = make_update(mocker, text="a" * 200)
    context = make_context(mocker)

    state = await get_country(update, context)

    assert "country" not in context.user_data
    assert state == PAYS


@pytest.mark.asyncio
async def test_get_city_and_weather_returns_weather_and_ends(mocker):
    update = make_update(mocker, text="Paris")
    context = make_context(mocker, user_data={"country": "France"})

    mocker.patch(
        "weather_bot.handlers.fetch_weather",
        mocker.AsyncMock(return_value="🌤️ Ensoleillé"),
    )

    state = await get_city_and_weather(update, context)

    context.bot.send_chat_action.assert_awaited_once()
    assert update.message.reply_text.await_count == 2
    assert state == ConversationHandler.END


@pytest.mark.asyncio
async def test_get_city_and_weather_rejects_invalid_input(mocker):
    update = make_update(mocker, text="")
    context = make_context(mocker, user_data={"country": "France"})

    fetch_mock = mocker.patch(
        "weather_bot.handlers.fetch_weather",
        mocker.AsyncMock(return_value="🌤️ Ensoleillé"),
    )

    state = await get_city_and_weather(update, context)

    fetch_mock.assert_not_awaited()
    assert state == VILLE


@pytest.mark.asyncio
async def test_get_city_and_weather_blocks_after_rate_limit(mocker):
    context = make_context(mocker, user_data={"country": "France"})
    fetch_mock = mocker.patch(
        "weather_bot.handlers.fetch_weather",
        mocker.AsyncMock(return_value="🌤️ Ensoleillé"),
    )

    # Épuise le quota autorisé
    for _ in range(RATE_LIMIT_MAX_REQUESTS):
        update = make_update(mocker, text="Paris", chat_id=999)
        await get_city_and_weather(update, context)

    fetch_mock.reset_mock()

    # La requête suivante doit être bloquée sans appeler l'API
    blocked_update = make_update(mocker, text="Paris", chat_id=999)
    state = await get_city_and_weather(blocked_update, context)

    fetch_mock.assert_not_awaited()
    assert state == ConversationHandler.END
    assert "Trop de requêtes" in blocked_update.message.reply_text.call_args.args[0]


@pytest.mark.asyncio
async def test_cancel_ends_conversation(mocker):
    update = make_update(mocker)
    context = make_context(mocker)

    state = await cancel(update, context)

    update.message.reply_text.assert_awaited_once()
    assert state == ConversationHandler.END


@pytest.mark.asyncio
async def test_timeout_ends_conversation(mocker):
    update = make_update(mocker)
    context = make_context(mocker)

    state = await timeout(update, context)

    update.message.reply_text.assert_awaited_once()
    assert state == ConversationHandler.END
