# setup_database.py

import sys
from pathlib import Path

# Füge src-Verzeichnis zum Python-Pfad hinzu
sys.path.append('src')

from sqlalchemy import create_engine
from models import Base


def setup_database():
    """Erstellt die Datenbank und Tabellen"""
    print("🔧 Setting up database...")

    # Erstelle src-Verzeichnis falls nicht vorhanden
    src_dir = Path("src")
    src_dir.mkdir(exist_ok=True)

    # Überprüfe ob models.py existiert
    models_file = src_dir / "models.py"
    if not models_file.exists():
        print("❌ models.py not found in src/ directory")
        print("Please create models.py with the provided schema")
        return

    # Erstelle Datenbank
    engine = create_engine("sqlite:///fiindo_challenge.db", echo=True)

    try:
        Base.metadata.create_all(engine)
        print("✅ Database created successfully: fiindo_challenge.db")

        print("\n📊 Database tables created:")
        for table in Base.metadata.tables.keys():
            print(f"  • {table}")

        print("\n➡️  Run Step 3 to store data:")
        print("    python step3_data_storage.py")

    except Exception as e:
        print(f"❌ Error creating database: {e}")


if __name__ == "__main__":
    setup_database()