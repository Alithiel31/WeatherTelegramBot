import pytest

from weather_bot.config import RATE_LIMIT_MAX_REQUESTS
from weather_bot.services.rate_limiter import is_rate_limited, _requests


@pytest.fixture(autouse=True)
def clear_rate_limiter():
    _requests.clear()
    yield
    _requests.clear()


def test_allows_requests_under_limit():
    chat_id = 111
    for _ in range(RATE_LIMIT_MAX_REQUESTS):
        assert is_rate_limited(chat_id) is False


def test_blocks_requests_over_limit():
    chat_id = 222
    for _ in range(RATE_LIMIT_MAX_REQUESTS):
        is_rate_limited(chat_id)

    assert is_rate_limited(chat_id) is True


def test_different_chats_have_independent_limits():
    chat_a, chat_b = 333, 444
    for _ in range(RATE_LIMIT_MAX_REQUESTS):
        is_rate_limited(chat_a)

    assert is_rate_limited(chat_a) is True
    assert is_rate_limited(chat_b) is False
