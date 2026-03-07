# Utilisation d'une image légère
FROM python:3.11-slim

# Empêche Python de générer des fichiers .pyc et permet l'affichage immédiat des logs
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Installation des dépendances système (uniquement si nécessaire pour certaines libs)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Installation des dépendances Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copie du reste du code
COPY . .

# Commande pour lancer le bot
CMD ["python", "main.py"]