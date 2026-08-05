## 🌤️ Telegram Weather Bot
A lightweight, asynchronous Telegram bot built with Python that provides real-time weather updates using the WeatherAPI. Users can simply send the name of a city and receive instant data on temperature, conditions, humidity, and wind speed.

## ✨ Features
- Real-time Data: Fetches current weather via WeatherAPI (HTTPS).
- Localized: Weather descriptions provided in French (lang=fr).
- User Friendly: Simple text-based interface (no complex commands needed).
- Robust Error Handling: Manages API timeouts and invalid city names gracefully.
- Asynchronous: Built on python-telegram-bot for efficient performance.
- Lightweight caching to avoid redundant API calls for the same city.
- Conversation auto-timeout to avoid stuck sessions.

## 🛠️ Installation & Setup
### 1. Prerequisites
- Python 3.10+
- A Telegram Bot Token (from @BotFather)
- A WeatherAPI Key (from WeatherAPI.com)

### 2. Clone the Repository
```bash
git clone https://github.com/<your-username>/WeatherTelegramBot.git
cd WeatherTelegramBot
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configuration
Copy `.env.example` to `.env` and add your credentials:
```bash
cp .env.example .env
```
```
TELEGRAM_TOKEN=your_telegram_bot_token_here
WEATHER_API_KEY=your_weatherapi_key_here
```

## 🚀 Usage
Run the bot using:
```bash
python main.py
```

How to interact with the bot:
1. Open Telegram and search for your bot.
2. Press /start.
3. Type a country, then a city name (e.g., France → Paris).
4. Receive a formatted weather report instantly!

## 🐳 Docker
```bash
docker compose up --build -d
```

## 🧪 Tests & Linting
```bash
pytest
black --check .
flake8 . --max-line-length=88
```

## 📦 Project Structure
- `main.py`: Bot bootstrap (builds the Telegram application and conversation handler).
- `config.py`: Environment variables and configuration constants.
- `weather_api.py`: WeatherAPI client (async fetch + in-memory cache).
- `handlers.py`: Telegram conversation handlers (start, get_country, get_city_and_weather, cancel, timeout).
- `tests/`: Unit tests for the weather API client and handlers.
- `.env`: Environment variables (ignored by git, see `.env.example`).
- `requirements.txt`: Pinned Python dependencies.

## 📝 Technical Details
The bot uses the `ApplicationBuilder` pattern from python-telegram-bot v20+. It includes a "typing" chat action to improve user experience while fetching data from the external API, an in-memory TTL cache to reduce redundant API calls, and a conversation timeout to automatically close inactive sessions.
