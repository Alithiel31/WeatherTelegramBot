# Changelog

All notable changes to this project are documented here.
Format inspired by [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

### Added

- Bilingual documentation suite: `README.fr.md`, `CONTRIBUTING.md`/`CONTRIBUTING.fr.md`, `Troubleshooting.md`/`Troubleshooting.fr.md`, this `CHANGELOG.md`
- Architecture diagram (Mermaid) and table of contents in the README
- `LICENSE` file (MIT)

### To do

- Consider structured/JSON logging to make the periodic metrics snapshot easier to scrape from outside the container
- Consider exposing the in-memory metrics over an HTTP endpoint (or Prometheus format) instead of log-only, if the bot ever needs external monitoring

## [0.4.0] - 2026-08-05

Hardening pass following the module split: fixes a healthcheck path that silently ignored `HEARTBEAT_FILE` overrides and a conversation-persistence path that didn't survive container recreation — see [`Troubleshooting.md`](./Troubleshooting.md) for both.

### Added

- Non-root Docker user (`botuser`); `/app/data` created and owned by it for the persistence volume
- `bot_data` named volume in `docker-compose.yml`, mounted at `/app/data`
- `PERSISTENCE_FILE` setting (`weather_bot/config.py`), defaulting to a path under the mounted volume in the Docker image
- `pytest.ini` coverage floor (`--cov-fail-under=90` on `weather_bot/`)
- `.pre-commit-config.yaml` (black, flake8, mypy) to reproduce CI checks locally before committing

### Fixed

- Dockerfile `HEALTHCHECK` had `/tmp/bot_heartbeat` hardcoded instead of reading `HEARTBEAT_FILE`, so overriding that variable had no effect on the healthcheck result
- Conversation state (`PicklePersistence`) defaulted to a relative path inside the container's writable layer, lost on `--force-recreate` instead of only on volume deletion

## [0.3.0] - 2026-08-05

Major refactor: single-file bot split into a proper package, with the security and resilience features the original script didn't have.

### Added

- Package layout: `weather_bot/config.py`, `weather_bot/handlers.py`, `weather_bot/services/` (`weather_api.py`, `rate_limiter.py`, `metrics.py`); `main.py` kept as the entry point
- Per-chat sliding-window rate limiting (`RATE_LIMIT_MAX_REQUESTS`, `RATE_LIMIT_WINDOW_SECONDS`) to prevent abuse and control WeatherAPI costs
- Bounded TTL cache (`cachetools`) on weather lookups (`WEATHER_CACHE_TTL`, `WEATHER_CACHE_MAXSIZE`)
- Retry with exponential backoff on transient network errors (`FETCH_MAX_RETRIES`, `FETCH_RETRY_BACKOFF_BASE`)
- Input validation and length limit on country/city messages (`MAX_INPUT_LENGTH`)
- Conversation auto-timeout (`CONVERSATION_TIMEOUT`) with a dedicated handler
- Thread-safe in-memory metrics (`weather_bot/services/metrics.py`), logged periodically (`METRICS_LOG_INTERVAL_SECONDS`)
- Docker `HEALTHCHECK` driven by a heartbeat file written by a background `JobQueue` job, instead of just checking that the process exists
- Specific handling for WeatherAPI error codes: 400 (place not found), 401/403 (invalid key, no retry), 429 (provider rate limit, no retry)
- Test suite covering handlers, rate limiter, and the weather client
- `mypy.ini`, `pip-audit` step

### Changed

- `.env` variables all made optional with documented defaults, except `TELEGRAM_TOKEN` and `WEATHER_API_KEY`

## [0.2.0] - 2026-03-07

### Added

- Unit tests for the initial single-file bot
- GitHub Actions CI workflow

### Fixed

- Code reformatted with `black`; `flake8` violations resolved
- CI workflow issues after the first setup attempt

## [0.1.0] - 2026-02-09

### Added

- Initial Telegram bot: single `main.py`, prompts for a country then a city, fetches current weather from WeatherAPI
- `README.md`
