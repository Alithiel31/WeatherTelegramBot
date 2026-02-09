# Utilisation d'une image légère adaptée au processeur du Raspberry Pi
FROM python:3.11-slim

# Définition du dossier de travail
WORKDIR /app

# Installation des dépendances système nécessaires
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copie et installation des bibliothèques Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copie du reste du code (bot.py et .env)
COPY . .

# Commande pour lancer le bot
CMD ["python", "bot.py"]