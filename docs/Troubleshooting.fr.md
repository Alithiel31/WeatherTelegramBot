# Dépannage

🇬🇧 [English version](./Troubleshooting.md)

Ce document retrace deux pièges de configuration rencontrés lors du durcissement de la config Docker, avec la démarche de diagnostic — pas seulement la solution finale. Les deux sont déjà corrigés dans le `Dockerfile`/`docker-compose.yml` actuels ; ce document existe pour que le même type de bug ne resurgisse pas silencieusement si `HEARTBEAT_FILE` ou `PERSISTENCE_FILE` est surchargé plus tard.

---

## 1. Le healthcheck Docker ignore `HEARTBEAT_FILE`

### Symptôme

Le bot écrit un fichier heartbeat toutes les `HEARTBEAT_INTERVAL_SECONDS` (30s par défaut) pour que le `HEALTHCHECK` Docker puisse distinguer un process réellement bloqué d'un process simplement inactif. Surcharger `HEARTBEAT_FILE` dans `.env` (par exemple pour le déplacer sous `/app/data`) n'avait aucun effet sur le résultat du healthcheck — le container continuait à se déclarer healthy ou unhealthy en se basant sur *l'ancien* chemin par défaut, quel que soit le chemin réellement utilisé par le bot.

### Investigation

```dockerfile
HEALTHCHECK --interval=60s --timeout=10s --start-period=30s --retries=3 \
    CMD find /tmp/bot_heartbeat -mmin -2 2>/dev/null | grep -q . || exit 1
```

Le `CMD` du `HEALTHCHECK` avait `/tmp/bot_heartbeat` codé en dur, alors que `weather_bot/config.py` lit ce même réglage depuis `HEARTBEAT_FILE`, ce chemin n'étant qu'une *valeur par défaut* :

```python
HEARTBEAT_FILE = os.getenv("HEARTBEAT_FILE", "/tmp/bot_heartbeat")
```

Deux sources de vérité indépendantes pour le même chemin : tant que `HEARTBEAT_FILE` restait à sa valeur par défaut, elles coïncidaient — ce qui a précisément rendu le bug facile à manquer.

### Root cause

Le `CMD` d'un `HEALTHCHECK` Dockerfile n'étend **pas** les variables shell/environnement, sauf s'il est lui-même écrit comme une expression shell qui le fait explicitement. Un simple `CMD find /tmp/bot_heartbeat ...` ne consulte jamais `HEARTBEAT_FILE`, quel que soit le contenu de l'environnement du container.

### Correction

Lire la même variable d'environnement dans la commande du healthcheck, avec la même valeur par défaut que `config.py` :

```dockerfile
HEALTHCHECK --interval=60s --timeout=10s --start-period=30s --retries=3 \
    CMD find "${HEARTBEAT_FILE:-/tmp/bot_heartbeat}" -mmin -2 2>/dev/null | grep -q . || exit 1
```

Si vous introduisez un autre réglage de type chemin que l'appli et le healthcheck (ou tout autre check hors-process) doivent partager, assurez-vous qu'il n'existe qu'une seule valeur par défaut, définie une seule fois, et que chaque consommateur lit la même variable d'environnement plutôt que de dupliquer le chemin en dur.

---

## 2. L'état de conversation ne survit pas à la recréation du container

### Symptôme

`PicklePersistence` est censé permettre à un flux `/start` en cours (pays déjà saisi, ville en attente) de survivre à un redémarrage du bot. En pratique, lancer `docker compose up -d --force-recreate` (ou toute opération qui recrée le container plutôt que de simplement redémarrer le process à l'intérieur) faisait silencieusement perdre toutes les conversations en cours.

### Investigation

Le chemin de persistance par défaut est relatif :

```python
PERSISTENCE_FILE = os.getenv("PERSISTENCE_FILE", "bot_persistence.pickle")
```

À l'intérieur du container, ce chemin se résout par rapport au répertoire de travail, `/app` (`WORKDIR /app` dans le `Dockerfile`) — un chemin qui vit dans la couche writable du container, pas sur un volume déclaré dans `docker-compose.yml`. Un `restart` conserve cette couche writable, donc la persistance semblait fonctionner en test superficiel ; une recréation (nouveau container, nouvelle couche writable) la fait disparaître, ce qui explique que le bug ne se soit manifesté qu'à un déploiement qui recréait le container au lieu de simplement le redémarrer.

### Root cause

Rien n'écrivait le fichier de persistance à un emplacement porté par un volume nommé — le chemin relatif par défaut ne survit que le temps de vie de l'instance de container concernée, ce qui n'est pas la garantie que `PicklePersistence` est censée offrir.

### Correction

Faire pointer `PERSISTENCE_FILE` vers un chemin sous un répertoire réellement monté, et déclarer ce volume :

```dockerfile
ENV PERSISTENCE_FILE=/app/data/bot_persistence.pickle
```

```yaml
# docker-compose.yml
volumes:
  - bot_data:/app/data
```

Ce même répertoire `/app/data` doit aussi appartenir à l'utilisateur non-root sous lequel tourne le container (`chown -R botuser:botuser /app` dans le `Dockerfile`, avant `USER botuser`) — sinon la correction de cet incident et le durcissement non-root seraient entrés silencieusement en conflit, le bot se retrouvant incapable d'écrire son propre fichier de persistance.
