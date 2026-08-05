# Contribuer

🇬🇧 [English version](./CONTRIBUTING.md)

Merci de votre intérêt pour ce projet. Ce dépôt est un bot Telegram météo (Python, `python-telegram-bot`) ; toute contribution qui corrige un bug, améliore la résilience/sécurité, ou améliore la documentation est bienvenue.

## Avant de commencer

- Ouvrez une issue pour discuter du changement envisagé, sauf pour les correctifs triviaux (typo, lien cassé).
- Vérifiez que le changement n'est pas déjà couvert par les éléments « To do » de [`CHANGELOG.md`](./CHANGELOG.md).

## Environnement de développement

```bash
git clone https://github.com/<votre-nom-utilisateur>/WeatherTelegramBot.git
cd WeatherTelegramBot
python -m venv .venv && source .venv/bin/activate   # optionnel mais recommandé
pip install -r requirements.txt
cp .env.example .env
# renseignez TELEGRAM_TOKEN et WEATHER_API_KEY
```

Les vérifications de la CI peuvent être reproduites en local :

```bash
black --check .                        # formatage
flake8 . --max-line-length=88           # analyse statique
mypy --ignore-missing-imports .         # vérification de types (voir mypy.ini pour les
                                         # deux exceptions et leur justification)
pytest                                  # tests + couverture, échoue sous 90% sur weather_bot/
pip-audit -r requirements.txt           # scan de vulnérabilités des dépendances
docker build -t weather-telegram-bot:local .   # confirme que l'image se construit toujours
```

Pour exécuter automatiquement ces mêmes vérifications avant chaque commit :

```bash
pip install pre-commit
pre-commit install
```

## Organisation du projet

`handlers.py` est la seule couche autorisée à manipuler `telegram.Update`/`ContextTypes` ; tout ce qui n'a pas besoin des objets Telegram va dans `weather_bot/services/`, et reste entièrement couvert par `mypy` (voir les exceptions accordées à `handlers.py` et `main.py` dans `mypy.ini`, qui existent parce que python-telegram-bot type certains attributs en `Optional` même quand nos filtres garantissent leur présence). Les tests dans `tests/` suivent la même organisation — ajoutez un test dans le fichier correspondant plutôt que d'en créer un nouveau, sauf si vous introduisez un nouveau module.

## Ouvrir une Pull Request

1. Créez une branche depuis `main` (`git checkout -b fix/mon-changement`).
2. Committez avec un message clair, idéalement au format `type: description` (`fix:`, `feat:`, `docs:`, `refactor:`, `chore:`...).
3. Mettez à jour [`CHANGELOG.md`](./CHANGELOG.md) dans la section `[Unreleased]` si le changement est notable pour un utilisateur ou opérateur du bot.
4. Vérifiez que le workflow CI passe (`test-and-lint`, `docker-build`).
5. Ouvrez la PR contre `main`.

## Signaler un problème

Lors de l'ouverture d'une issue, merci d'inclure : les lignes de log pertinentes (`docker logs telegram_weather_bot` si le bot tourne via Docker), si le problème survient avec les réglages par défaut ou après surcharge de `HEARTBEAT_FILE`/`PERSISTENCE_FILE`/autres variables, et votre version de Python ou de Docker. Consultez d'abord [`Troubleshooting.fr.md`](./Troubleshooting.fr.md) — deux pièges de configuration impliquant ces deux variables y sont déjà documentés.

Ne collez jamais un vrai `TELEGRAM_TOKEN` ou `WEATHER_API_KEY` dans une issue ; masquez-les dans tout log ou config que vous copiez.

## Secrets

Ne committez jamais `.env` ni une vraie valeur de `TELEGRAM_TOKEN` ou `WEATHER_API_KEY`. Faites tourner un token immédiatement en cas de fuite (via @BotFather pour Telegram, via votre dashboard WeatherAPI pour la clé météo).
