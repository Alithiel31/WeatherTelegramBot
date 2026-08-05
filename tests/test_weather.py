import httpx
import pytest

from weather_bot.services import weather_api
from weather_bot.services.weather_api import fetch_weather, _cache


@pytest.fixture(autouse=True)
def clear_cache():
    _cache.clear()
    yield
    _cache.clear()


@pytest.mark.asyncio
async def test_fetch_weather_success(mocker):
    # On simule la réponse de l'API
    mock_response = mocker.Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "location": {"name": "Paris", "country": "France"},
        "current": {
            "condition": {"text": "Ensoleillé"},
            "temp_c": 20.5,
            "humidity": 45,
            "wind_kph": 15,
        },
    }

    mocker.patch("httpx.AsyncClient.get", return_value=mock_response)

    result = await fetch_weather("Paris", "France")

    assert "Paris" in result
    assert "20.5°C" in result
    assert "Ensoleillé" in result


@pytest.mark.asyncio
async def test_fetch_weather_error(mocker):
    # On simule une erreur 400 (ville non trouvée)
    mock_response = mocker.Mock()
    mock_response.status_code = 400
    mocker.patch("httpx.AsyncClient.get", return_value=mock_response)

    result = await fetch_weather("VilleInexistante", "PaysFaux")
    assert "Lieu non trouvé" in result


@pytest.mark.asyncio
async def test_fetch_weather_invalid_api_key(mocker):
    mock_response = mocker.Mock()
    mock_response.status_code = 401
    mocker.patch("httpx.AsyncClient.get", return_value=mock_response)

    result = await fetch_weather("Paris", "France")
    assert "Configuration du service météo invalide" in result


@pytest.mark.asyncio
async def test_fetch_weather_rate_limited_by_provider(mocker):
    mock_response = mocker.Mock()
    mock_response.status_code = 429
    mocker.patch("httpx.AsyncClient.get", return_value=mock_response)

    result = await fetch_weather("Paris", "France")
    assert "surchargé" in result


@pytest.mark.asyncio
async def test_fetch_weather_uses_https(mocker):
    mock_response = mocker.Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "location": {"name": "Tokyo", "country": "Japan"},
        "current": {
            "condition": {"text": "Nuageux"},
            "temp_c": 18.0,
            "humidity": 60,
            "wind_kph": 10,
        },
    }
    mock_get = mocker.patch("httpx.AsyncClient.get", return_value=mock_response)

    await fetch_weather("Tokyo", "Japan")

    called_url = mock_get.call_args.args[0]
    assert called_url.startswith("https://")


@pytest.mark.asyncio
async def test_fetch_weather_encodes_special_characters(mocker):
    mock_response = mocker.Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "location": {"name": "New York", "country": "USA"},
        "current": {
            "condition": {"text": "Clear"},
            "temp_c": 22.0,
            "humidity": 40,
            "wind_kph": 5,
        },
    }
    mock_get = mocker.patch("httpx.AsyncClient.get", return_value=mock_response)

    await fetch_weather("New York", "USA")

    called_url = mock_get.call_args.args[0]
    assert " " not in called_url


@pytest.mark.asyncio
async def test_fetch_weather_cache_avoids_second_call(mocker):
    mock_response = mocker.Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "location": {"name": "Paris", "country": "France"},
        "current": {
            "condition": {"text": "Ensoleillé"},
            "temp_c": 20.5,
            "humidity": 45,
            "wind_kph": 15,
        },
    }
    mock_get = mocker.patch("httpx.AsyncClient.get", return_value=mock_response)

    await fetch_weather("Paris", "France")
    await fetch_weather("Paris", "France")

    assert mock_get.call_count == 1


@pytest.mark.asyncio
async def test_fetch_weather_retries_on_network_error(mocker):
    mocker.patch("weather_bot.services.weather_api.asyncio.sleep", mocker.AsyncMock())
    mock_get = mocker.patch(
        "httpx.AsyncClient.get", side_effect=httpx.ConnectTimeout("timeout")
    )

    result = await fetch_weather("Paris", "France")

    assert mock_get.call_count == weather_api.FETCH_MAX_RETRIES
    assert "Impossible de contacter" in result


@pytest.mark.asyncio
async def test_fetch_weather_recovers_after_transient_error(mocker):
    mocker.patch("weather_bot.services.weather_api.asyncio.sleep", mocker.AsyncMock())

    mock_response = mocker.Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "location": {"name": "Paris", "country": "France"},
        "current": {
            "condition": {"text": "Ensoleillé"},
            "temp_c": 20.5,
            "humidity": 45,
            "wind_kph": 15,
        },
    }

    mock_get = mocker.patch(
        "httpx.AsyncClient.get",
        side_effect=[httpx.ConnectTimeout("timeout"), mock_response],
    )

    result = await fetch_weather("Paris", "France")

    assert mock_get.call_count == 2
    assert "Paris" in result


@pytest.mark.asyncio
async def test_fetch_weather_unexpected_schema(mocker):
    mock_response = mocker.Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"unexpected": "schema"}
    mocker.patch("httpx.AsyncClient.get", return_value=mock_response)

    result = await fetch_weather("Paris", "France")
    assert "erreur technique" in result
