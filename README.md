## 🌤️ Telegram Weather Bot
A lightweight, asynchronous Telegram bot built with Python that provides real-time weather updates using the WeatherAPI. Users can simply send the name of a city and receive instant data on temperature, conditions, humidity, and wind speed.

## ✨ Features
- Real-time Data: Fetches current weather via WeatherAPI.
- Localized: Weather descriptions provided in French (lang=fr).
- User Friendly: Simple text-based interface (no complex commands needed).
- Robust Error Handling: Manages API timeouts and invalid city names gracefully.
- Asynchronous: Built on python-telegram-bot for efficient performance.

## 🛠️ Installation & Setup
### 1. Prerequisites
- Python 3.10+
- A Telegram Bot Token (from @BotFather)
- A WeatherAPI Key (from WeatherAPI.com)

### 2. Clone the Repository
Bash
git clone https://github.com/yourusername/weather-telegram-bot.git
cd weather-telegram-bot
3. Install Dependencies
Bash
pip install python-telegram-bot requests python-dotenv
4. Configuration
Create a .env file in the root directory and add your credentials:

Extrait de code
TELEGRAM_TOKEN=your_telegram_bot_token_here
WEATHER_API_KEY=your_weatherapi_key_here

## 🚀 Usage
***Run the bot using:***
Bash
python main.py
How to interact with the bot:

Open Telegram and search for your bot.

Press /start.

Type any city name (e.g., Paris, Tokyo, or New York).

Receive a formatted weather report instantly!

## 📦 Project Structure
main.py: The core application logic and Telegram handlers.

.env: Environment variables (ignored by git).

requirements.txt: List of Python dependencies.

## 📝 Technical Details
The bot utilizes the ApplicationBuilder pattern from python-telegram-bot v20+. It includes a "typing" chat action to improve user experience while fetching data from the external API.