# find_data_files.py

import json
from pathlib import Path
from datetime import datetime


def list_all_data_files():
    """Listet alle Daten-Dateien auf"""
    print("=" * 70)
    print("AVAILABLE DATA FILES")
    print("=" * 70)

    data_dir = Path("data")

    if not data_dir.exists():
        print("❌ data/ Verzeichnis existiert nicht!")
        return

    # Alle Dateien
    all_files = list(data_dir.glob("*"))

    if not all_files:
        print("📭 data/ Verzeichnis ist leer!")
        return

    print(f"📂 Gefundene Dateien ({len(all_files)}):")

    financial_data_files = []

    for i, file in enumerate(sorted(all_files), 1):
        size_mb = file.stat().st_size / (1024 * 1024)
        mod_time = datetime.fromtimestamp(file.stat().st_mtime)

        print(f"\n{i:2d}. {file.name}")
        print(f"    Größe: {size_mb:.2f} MB")
        print(f"    Geändert: {mod_time}")

        # Check file type
        if file.suffix == ".json":
            try:
                with open(file, "r") as f:
                    data = json.load(f)

                if isinstance(data, dict):
                    if any(symbol in str(data.keys()) for symbol in ["AAPL", "JPM", "NVDA", "MSFT"]):
                        print(f"    ✅ Vermutlich Financial Data")
                        financial_data_files.append(file)
                    elif "symbols" in data:
                        print(f"    📋 Symbols List ({len(data.get('symbols', []))} symbols)")
                    else:
                        print(f"    📊 JSON Dict mit {len(data)} Einträgen")
                elif isinstance(data, list):
                    print(f"    📋 JSON Liste mit {len(data)} Elementen")

            except json.JSONDecodeError:
                print(f"    ❌ Ungültiges JSON")
            except Exception as e:
                print(f"    ⚠️  Fehler: {e}")
        elif file.suffix == ".db":
            print(f"    🗄️  SQLite Database")

    return financial_data_files


def get_latest_financial_data():
    """Findet die neueste financial_data Datei"""
    print("\n" + "=" * 70)
    print("LATEST FINANCIAL DATA SEARCH")
    print("=" * 70)

    data_dir = Path("data")

    # Suche nach allen möglichen financial data Dateien
    patterns = [
        "financial_data_*.json",
        "*financial*.json",
        "*data_*.json",
        "ticker_statistics_*.json"
    ]

    all_financial_files = []
    for pattern in patterns:
        all_financial_files.extend(data_dir.glob(pattern))

    if not all_financial_files:
        print("❌ Keine Financial Data Dateien gefunden!")
        return None

    # Sortiere nach Änderungsdatum (neueste zuerst)
    sorted_files = sorted(all_financial_files, key=lambda x: x.stat().st_mtime, reverse=True)

    print(f"📊 Gefundene Financial Data Dateien ({len(sorted_files)}):")
    for i, file in enumerate(sorted_files[:5], 1):  # Zeige nur top 5
        size_mb = file.stat().st_size / (1024 * 1024)
        mod_time = datetime.fromtimestamp(file.stat().st_mtime)
        print(f"  {i}. {file.name} ({size_mb:.2f} MB, {mod_time})")

    latest = sorted_files[0]
    print(f"\n✅ Neueste Datei: {latest.name}")

    # Dateiinhalt prüfen
    try:
        with open(latest, "r") as f:
            data = json.load(f)

        print(f"📋 Dateiinhalt:")
        if isinstance(data, dict):
            print(f"  • Typ: Dictionary")
            print(f"  • Einträge: {len(data)}")
            if data:
                keys = list(data.keys())
                print(f"  • Erste 3 Keys: {keys[:3]}")

                # Zeige ersten Eintrag
                first_key = keys[0]
                first_value = data[first_key]
                if isinstance(first_value, dict):
                    print(f"  • Erster Eintrag ({first_key}):")
                    print(f"    Keys: {list(first_value.keys())}")
        elif isinstance(data, list):
            print(f"  • Typ: Liste")
            print(f"  • Elemente: {len(data)}")
            if data:
                first_item = data[0]
                if isinstance(first_item, dict):
                    print(f"  • Erstes Element Keys: {list(first_item.keys())}")

    except Exception as e:
        print(f"❌ Fehler beim Lesen: {e}")

    return latest


if __name__ == "__main__":
    list_all_data_files()
    latest_file = get_latest_financial_data()

    if latest_file:
        print(f"\n💡 Verwenden Sie diese Datei in Ihren Skripten:")
        print(f'   data_file = Path("data/{latest_file.name}")')