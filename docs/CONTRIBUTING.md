# Contributing

🇫🇷 [Version française](./CONTRIBUTING.fr.md)

Thanks for your interest in this project. This repository is a Telegram weather bot (Python, `python-telegram-bot`); any contribution that fixes a bug, improves resilience/security, or improves the documentation is welcome.

## Before you start

- Open an issue to discuss the change you have in mind, except for trivial fixes (typo, broken link).
- Check that the change is not already covered by the "To do" items in [`CHANGELOG.md`](./CHANGELOG.md).

## Development environment

```bash
git clone https://github.com/<your-username>/WeatherTelegramBot.git
cd WeatherTelegramBot
python -m venv .venv && source .venv/bin/activate   # optional but recommended
pip install -r requirements.txt
cp .env.example .env
# fill in TELEGRAM_TOKEN and WEATHER_API_KEY
```

The CI checks can be reproduced locally:

```bash
black --check .                        # formatting
flake8 . --max-line-length=88           # static analysis
mypy --ignore-missing-imports .         # type checking (see mypy.ini for the two
                                         # relaxed exceptions and why)
pytest                                  # tests + coverage, fails under 90% on weather_bot/
pip-audit -r requirements.txt           # dependency vulnerability scan
docker build -t weather-telegram-bot:local .   # confirms the image still builds
```

To run the same checks automatically before every commit:

```bash
pip install pre-commit
pre-commit install
```

## Project layout

`handlers.py` is the only layer allowed to talk to `telegram.Update`/`ContextTypes`; anything that doesn't need Telegram objects belongs in `weather_bot/services/`, and stays fully covered by `mypy` (see the exceptions carved out for `handlers.py` and `main.py` in `mypy.ini`, which exist because python-telegram-bot types some attributes as `Optional` even where our filters guarantee they're present). Tests in `tests/` mirror this layout — add a test in the matching file rather than a new one unless you're introducing a new module.

## Opening a Pull Request

1. Create a branch from `main` (`git checkout -b fix/my-change`).
2. Commit with a clear message, ideally in the `type: description` format (`fix:`, `feat:`, `docs:`, `refactor:`, `chore:`...).
3. Update [`CHANGELOG.md`](./CHANGELOG.md) in the `[Unreleased]` section if the change is notable for a user or operator of the bot.
4. Check that the CI workflow passes (`test-and-lint`, `docker-build`).
5. Open the PR against `main`.

## Reporting a problem

When opening an issue, please include: the relevant log lines (`docker logs telegram_weather_bot` if running via Docker), whether the issue happens with default settings or after overriding `HEARTBEAT_FILE`/`PERSISTENCE_FILE`/other env vars, and your Python or Docker version. Check [`Troubleshooting.md`](./Troubleshooting.md) first — two config pitfalls involving those two variables are already documented there.

Never paste a real `TELEGRAM_TOKEN` or `WEATHER_API_KEY` in an issue; redact them from any log or config you copy in.

## Secrets

Never commit `.env` or any real value of `TELEGRAM_TOKEN` or `WEATHER_API_KEY`. Rotate a token immediately if it leaks (via @BotFather for Telegram, via your WeatherAPI dashboard for the weather key).
