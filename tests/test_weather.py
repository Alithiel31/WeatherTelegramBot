import pytest
from main import fetch_weather


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
