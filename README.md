## 🌤️ Telegram Weather Bot
A lightweight, asynchronous Telegram bot built with Python that provides real-time weather updates using the WeatherAPI. Users can simply send the name of a city and receive instant data on temperature, conditions, humidity, and wind speed.

## ✨ Features
- Real-time Data: Fetches current weather via WeatherAPI (HTTPS).
- Localized: Weather descriptions provided in French (lang=fr).
- User Friendly: Simple text-based interface (no complex commands needed).
- Robust Error Handling: Manages API timeouts, invalid city names, invalid API keys (401/403), and provider rate limits (429) gracefully.
- Automatic retry with exponential backoff on transient network errors.
- Per-chat rate limiting to prevent abuse and control API costs.
- Input validation on country/city messages.
- Asynchronous: Built on python-telegram-bot for efficient performance.
- Bounded TTL caching (cachetools) to avoid redundant API calls for the same city.
- Conversation auto-timeout to avoid stuck sessions.
- Basic in-memory metrics (requests, cache hits, errors, rate-limited) logged periodically.
- Docker healthcheck based on a real activity heartbeat, not just process presence.
- Conversation state persisted to disk (survives bot restarts when the file is on a mounted volume).
- Container runs as a non-root user.

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

Optional tuning variables (sensible defaults are used if omitted):
```
CONVERSATION_TIMEOUT=300           # seconds before an inactive conversation closes
WEATHER_CACHE_TTL=600               # seconds a cached weather result stays valid
WEATHER_CACHE_MAXSIZE=500           # max distinct city/country entries cached
RATE_LIMIT_MAX_REQUESTS=5           # max weather requests per chat per window
RATE_LIMIT_WINDOW_SECONDS=60        # sliding window size for rate limiting
MAX_INPUT_LENGTH=60                 # max characters accepted for country/city input
FETCH_MAX_RETRIES=3                 # retry attempts on transient network errors
FETCH_RETRY_BACKOFF_BASE=0.5        # base delay (seconds) for exponential backoff
METRICS_LOG_INTERVAL_SECONDS=3600   # how often metrics are logged
HEARTBEAT_FILE=/tmp/bot_heartbeat   # heartbeat file used by the Docker healthcheck
HEARTBEAT_INTERVAL_SECONDS=30       # how often the heartbeat file is updated
PERSISTENCE_FILE=bot_persistence.pickle  # where in-progress conversations are saved
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
pytest                                 # runs tests + coverage (min. 90% on weather_bot/)
black --check .
flake8 . --max-line-length=88
mypy --ignore-missing-imports .
pip-audit -r requirements.txt
```

To run the same checks automatically before every commit:
```bash
pip install pre-commit
pre-commit install
```

## 📦 Project Structure
The app follows a light layered structure: `handlers.py` is the presentation layer (talks to Telegram), `services/` is framework-agnostic business logic, `config.py` is shared configuration. `main.py` stays at the repository root as the entry point.

```
WeatherTelegramBot/
├── main.py                    # Bot bootstrap: app, conversation handler, background jobs
├── weather_bot/
│   ├── config.py              # Environment variables and configuration constants
│   ├── handlers.py            # Telegram conversation handlers (start, get_country, ...)
│   └── services/
│       ├── weather_api.py     # WeatherAPI client (async fetch, TTL cache, retry/backoff)
│       ├── rate_limiter.py    # Per-chat sliding-window rate limiter
│       └── metrics.py         # Thread-safe in-memory counters
├── tests/                     # Unit tests mirroring the package layout
├── .env                       # Environment variables (ignored by git, see .env.example)
├── requirements.txt           # Pinned Python dependencies
├── pytest.ini                 # Test config: pythonpath + coverage threshold
├── .pre-commit-config.yaml    # Local pre-commit hooks (black, flake8, mypy)
└── .github/
    ├── workflows/ci.yml       # CI: lint, type-check, tests, dependency audit, Docker build
    └── dependabot.yml         # Automated dependency update PRs (pip, GitHub Actions, Docker)
```

## 📝 Technical Details
The bot uses the `ApplicationBuilder` pattern from python-telegram-bot v20+. It includes a "typing" chat action to improve user experience while fetching data from the external API, a bounded in-memory TTL cache (`cachetools`) to reduce redundant API calls, automatic retry with exponential backoff on transient network failures, per-chat rate limiting, and a conversation timeout to automatically close inactive sessions. A background `JobQueue` job writes a heartbeat file used by the Docker `HEALTHCHECK` to confirm the bot is actually alive (not just that the process exists), and periodically logs basic usage metrics. Conversation state is persisted via `PicklePersistence` so an in-progress `/start` flow survives a bot restart, provided `PERSISTENCE_FILE` points to a mounted volume (see `docker-compose.yml`). The Docker image drops root privileges before running the bot.
