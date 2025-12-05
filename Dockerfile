# Python 3.11 Basis-Image
FROM python:3.11-slim

# Arbeitsverzeichnis im Container
WORKDIR /app

# System-Abhängigkeiten (falls nötig für SQLite)
RUN apt-get update && apt-get install -y \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Abhängigkeiten kopieren und installieren
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Anwendungscode kopieren
COPY . .

# Datenbank-Verzeichnis erstellen
RUN mkdir -p /app/data

# Port (wenn Ihr App einen braucht, z.B. für Web-API)
EXPOSE 8000

# Startbefehl
CMD ["python", "main.py"]