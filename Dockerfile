# Étape 1: Image temporaire pour installer les dépendances
FROM python:3.10.0 as builder

WORKDIR /build

# Copie uniquement le fichier requirements.txt
COPY requirements.txt .

# Installation des dépendances dans un dossier temporaire
RUN pip install --no-cache-dir --target=/build/dependencies -r requirements.txt

# Étape 2: Image finale
FROM python:3.10.0

WORKDIR /app

# Copie des dépendances depuis l'image temporaire
COPY --from=builder /build/dependencies /app/dependencies

# Copie du reste du projet dans l'image finale
COPY . /app

# Installation des dépendances du projet
RUN pip install --no-cache-dir -r /app/requirements.txt

# Démarrer le projet
CMD [ "python", "app.py" ]