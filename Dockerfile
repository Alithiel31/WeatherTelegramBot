# Utilisation d'une image légère
FROM python:3.11-slim

# Empêche Python de générer des fichiers .pyc et permet l'affichage immédiat des logs
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# procps fournit pgrep, utilisé par le HEALTHCHECK ci-dessous
# (pas de build-essential : aucune dépendance Python ne nécessite de compilation native)
RUN apt-get update && apt-get install -y --no-install-recommends \
    procps \
    && rm -rf /var/lib/apt/lists/*

# Installation des dépendances Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copie du reste du code
COPY . .

# Vérifie que le process Python du bot tourne toujours
HEALTHCHECK --interval=60s --timeout=10s --start-period=15s --retries=3 \
    CMD pgrep -f "python main.py" || exit 1

# Commande pour lancer le bot
CMD ["python", "main.py"]