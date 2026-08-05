# Troubleshooting

🇫🇷 [Version française](./Troubleshooting.fr.md)

This document covers two configuration pitfalls found while hardening the Docker setup, with the diagnosis path — not just the fix. Both are already corrected in the current `Dockerfile`/`docker-compose.yml`; this is here so the same class of bug doesn't quietly resurface if `HEARTBEAT_FILE` or `PERSISTENCE_FILE` is overridden later.

---

## 1. Docker healthcheck ignoring `HEARTBEAT_FILE`

### Symptom

The bot writes a heartbeat file every `HEARTBEAT_INTERVAL_SECONDS` (30s by default) so Docker's `HEALTHCHECK` can tell a genuinely stuck process from one that's merely quiet. Overriding `HEARTBEAT_FILE` in `.env` (for example to move it under `/app/data`) had no effect on the healthcheck result — the container kept reporting healthy or unhealthy based on the *old* default path, regardless of what the bot actually wrote to.

### Investigation

```dockerfile
HEALTHCHECK --interval=60s --timeout=10s --start-period=30s --retries=3 \
    CMD find /tmp/bot_heartbeat -mmin -2 2>/dev/null | grep -q . || exit 1
```

The `HEALTHCHECK CMD` had `/tmp/bot_heartbeat` hardcoded, while `weather_bot/config.py` reads the same setting from `HEARTBEAT_FILE` with that path only as a *default*:

```python
HEARTBEAT_FILE = os.getenv("HEARTBEAT_FILE", "/tmp/bot_heartbeat")
```

Two independent sources of truth for the same path: as long as `HEARTBEAT_FILE` was left at its default they happened to agree, which is exactly what made the bug easy to miss.

### Root cause

`CMD` in a Dockerfile `HEALTHCHECK` does **not** expand shell/environment variables unless it is itself written as a shell expression that does so explicitly. A bare `CMD find /tmp/bot_heartbeat ...` never looks at `HEARTBEAT_FILE`, no matter what the container's environment contains.

### Fix

Read the same environment variable in the healthcheck command, with the same default as `config.py`:

```dockerfile
HEALTHCHECK --interval=60s --timeout=10s --start-period=30s --retries=3 \
    CMD find "${HEARTBEAT_FILE:-/tmp/bot_heartbeat}" -mmin -2 2>/dev/null | grep -q . || exit 1
```

If you introduce another path-like setting that both the app and the healthcheck (or any other out-of-process check) need to agree on, make sure there is exactly one default, defined once, and that every consumer reads the same environment variable rather than duplicating the literal path.

---

## 2. Conversation state not surviving container recreation

### Symptom

`PicklePersistence` is meant to let an in-progress `/start` flow (country already given, waiting on the city) survive a bot restart. In practice, running `docker compose up -d --force-recreate` (or any operation that recreates the container rather than just restarting the process inside it) silently dropped all in-progress conversations.

### Investigation

The default persistence path is relative:

```python
PERSISTENCE_FILE = os.getenv("PERSISTENCE_FILE", "bot_persistence.pickle")
```

Inside the container this resolves against the working directory, `/app` (`WORKDIR /app` in the `Dockerfile`) — a path that lives in the container's writable layer, not on any volume declared in `docker-compose.yml`. A `restart` keeps that writable layer, so persistence appeared to work in casual testing; a recreate (new container, fresh writable layer) discards it, which is why the bug didn't show up until a deploy that happened to recreate the container instead of just restarting it.

### Root cause

Nothing wrote the persistence file to a location backed by a named volume — the default relative path only survives as long as the specific container instance does, which is not the guarantee `PicklePersistence` is supposed to provide.

### Fix

Point `PERSISTENCE_FILE` at a path under a directory that's actually mounted, and declare that volume:

```dockerfile
ENV PERSISTENCE_FILE=/app/data/bot_persistence.pickle
```

```yaml
# docker-compose.yml
volumes:
  - bot_data:/app/data
```

The same `/app/data` directory also needs to be owned by the non-root user the container runs as (`chown -R botuser:botuser /app` in the `Dockerfile`, before `USER botuser`) — otherwise the fix for this incident and the non-root hardening would have silently conflicted, with the bot unable to write its own persistence file.
