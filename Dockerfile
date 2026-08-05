# Utilisation d'une image légère
FROM python:3.11-slim

# Empêche Python de générer des fichiers .pyc et permet l'affichage immédiat des logs
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# findutils fournit find, utilisé par le HEALTHCHECK ci-dessous
# (pas de build-essential : aucune dépendance Python ne nécessite de compilation native)
RUN apt-get update && apt-get install -y --no-install-recommends \
    findutils \
    && rm -rf /var/lib/apt/lists/*

# Installation des dépendances Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copie du reste du code
COPY . .

# Vérifie que le bot est réellement actif : le process écrit un fichier
# heartbeat toutes les HEARTBEAT_INTERVAL_SECONDS (30s par défaut). S'il n'a
# pas été mis à jour depuis 2 minutes, le bot est considéré comme bloqué.
HEALTHCHECK --interval=60s --timeout=10s --start-period=30s --retries=3 \
    CMD find /tmp/bot_heartbeat -mmin -2 2>/dev/null | grep -q . || exit 1

# Commande pour lancer le bot
CMD ["python", "main.py"]