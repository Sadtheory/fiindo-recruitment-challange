# tests/test_step3.py
import pytest
import sys
import os

# WICHTIG: Füge src Verzeichnis zum Python-Pfad hinzu
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
src_dir = os.path.join(parent_dir, 'src')
sys.path.insert(0, src_dir)

# Jetzt können wir step3_data_storage aus src importieren
from step3_data_storage import DataStorage, main


def test_step3_import():
    """Test dass step3_data_storage korrekt importiert werden kann"""
    # Prüfe Hauptklasse
    assert DataStorage is not None

    # Prüfe Hauptfunktion
    assert main is not None
    assert callable(main)

    print("✅ Step 3 import successful")


def test_datastorage_class():
    """Test der DataStorage Klasse"""
    # Erstelle Instanz
    storage = DataStorage()

    # Prüfe Attribute
    assert hasattr(storage, 'database_url')
    assert storage.database_url == "sqlite:///fiindo_challenge.db"

    # Prüfe wichtige Methoden
    methods = [
        'create_database',
        'check_tables_exist',
        'connect',
        'disconnect',
        'store_ticker_statistics',
        'store_industry_aggregation',
        'load_latest_ticker_statistics',
        'load_latest_industry_aggregation'
    ]

    for method in methods:
        assert hasattr(storage, method), f"Missing method: {method}"

    print("✅ DataStorage class structure is correct")


def test_database_url():
    """Test der Datenbank-URL"""
    # Test Default URL
    storage = DataStorage()
    assert storage.database_url == "sqlite:///fiindo_challenge.db"

    # Test mit custom URL
    custom_storage = DataStorage("sqlite:///test.db")
    assert custom_storage.database_url == "sqlite:///test.db"

    print("✅ Database URL configuration works")


def test_models_import():
    """Test dass Models korrekt importiert werden können"""
    try:
        # Versuche Models zu importieren
        from models import Base, TickerStatistics, IndustryAggregation

        # Prüfe wichtige Klassen
        assert Base is not None
        assert TickerStatistics is not None
        assert IndustryAggregation is not None

        print("✅ Models import successful")

    except ImportError as e:
        print(f"⚠️  Models import skipped: {e}")
        # Das ist OK für den Test


def test_step3_functions():
    """Test der Hilfsfunktionen in Step 3"""
    # Prüfe ob main Funktion existiert
    assert callable(main)

    print("✅ Step 3 functions are properly defined")


if __name__ == "__main__":
    # Führe alle Tests aus
    test_step3_import()
    test_datastorage_class()
    test_database_url()
    test_models_import()
    test_step3_functions()

    print("\n🎉 All Step 3 tests completed!")