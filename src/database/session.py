# src/database/session.py

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import os
from pathlib import Path

# Datenbankpfad
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)  # Erstellt Ordner falls nicht existiert
DATABASE_URL = f"sqlite:///{DATA_DIR}/fiindo_challenge.db"

# Engine und Session erstellen
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # Wichtig für SQLite
    echo=False  # Auf True setzen für SQL-Ausgaben (nur im Debug)
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Dependency für Datenbank-Sessions
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()