# src/utils/config.py

import os
from pathlib import Path
from dotenv import load_dotenv

# Lade .env Datei
load_dotenv()

# Basis-Pfad
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# API-Einstellungen
API_BASE_URL = "https://api.test.fiindo.com"
API_DOCS_URL = "https://api.test.fiindo.com/api/v1/docs/"

# Authentifizierung (aus .env oder Umgebungsvariablen)
FIRST_NAME = os.getenv("FIRST_NAME", "")
LAST_NAME = os.getenv("LAST_NAME", "")
BEARER_TOKEN = f"{FIRST_NAME}.{LAST_NAME}"

# Ziel-Industrien (per Challenge)
TARGET_INDUSTRIES = [
    "Banks - Diversified",
    "Software - Application",
    "Consumer Electronics"
]

# Datenbank
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)
DATABASE_PATH = DATA_DIR / "fiindo_challenge.db"
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

# Logging
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "app.log"

# API Endpoints (basierend auf Dokumentation - müssen Sie prüfen!)
API_ENDPOINTS = {
    "tickers": "/api/v1/tickers",
    "financials": "/api/v1/financials",
    "industries": "/api/v1/industries",
}

# Debug-Modus
DEBUG = os.getenv("DEBUG", "False").lower() == "true"

# API Limits
REQUEST_TIMEOUT = 30  # seconds
MAX_RETRIES = 3