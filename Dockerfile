# Étape 1: Image temporaire pour installer les dépendances
FROM python:3.12.8-alpine3.21 AS builder

WORKDIR /build

# Copie uniquement le fichier requirements.txt
COPY requirements.txt .

# Installation des dépendances dans un dossier temporaire
RUN pip install --no-cache-dir --target=/build/dependencies -r requirements.txt

# Étape 2: Image finale
FROM python:3.12.8-alpine3.21

WORKDIR /app

# Copie des dépendances depuis l'image temporaire
COPY --from=builder /build/dependencies /app/dependencies

# Copie du reste du projet dans l'image finale
COPY . /app

# Installation des dépendances du projet
RUN pip install --no-cache-dir -r /app/requirements.txt

# Démarrer le projet
CMD [ "python", "main.py" ]

# Commande pour lancer l'execution de l'application dans le container
# docker run --mount type=bind,source=config.json,target=/app/config.json \
#  --mount type=bind,source=metadata,target=/app/metadata \
#  --mount type=bind,source=old_metadata,target=/app/old_metadata \
#  --mount type=bind,source=source,target=/app/sources \
#  --mount type=bind,source=processing,target=/app/processing \
#  --mount type=bind,source=results,target=/app/results \
#  --mount type=bind,source=data,target=/app/data docker-decp-rama