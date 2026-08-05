import pytest
from telegram.ext import ConversationHandler

from config import PAYS, VILLE
from handlers import start, get_country, get_city_and_weather, cancel, timeout


def make_update(mocker, text=None):
    update = mocker.Mock()
    update.message = mocker.Mock()
    update.message.text = text
    update.message.reply_text = mocker.AsyncMock()
    update.effective_chat = mocker.Mock()
    update.effective_chat.id = 123
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
async def test_get_city_and_weather_returns_weather_and_ends(mocker):
    update = make_update(mocker, text="Paris")
    context = make_context(mocker, user_data={"country": "France"})

    mocker.patch(
        "handlers.fetch_weather", mocker.AsyncMock(return_value="🌤️ Ensoleillé")
    )

    state = await get_city_and_weather(update, context)

    context.bot.send_chat_action.assert_awaited_once()
    assert update.message.reply_text.await_count == 2
    assert state == ConversationHandler.END


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
