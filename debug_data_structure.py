# debug_data_structure.py

import json
from pathlib import Path


def debug_data():
    """Debuggt die Datenstruktur detailliert"""
    print("=" * 70)
    print("DETAILED DATA DEBUGGING")
    print("=" * 70)

    data_file = Path("data/financial_data_20251206_182246.json")

    with open(data_file, "r") as f:
        data = json.load(f)

    print(f"Symbole: {list(data.keys())}")

    for symbol, symbol_data in data.items():
        print(f"\n{'=' * 50}")
        print(f"SYMBOL: {symbol}")
        print(f"{'=' * 50}")

        industry = symbol_data.get("industry", "Not found")
        print(f"Industry: {industry}")

        # Durchsuche ALLE Keys rekursiv
        def search_for_values(obj, path=""):
            results = []

            if isinstance(obj, dict):
                for key, value in obj.items():
                    new_path = f"{path}.{key}" if path else key

                    # Suche nach wichtigen Keywords
                    key_lower = str(key).lower()
                    if any(term in key_lower for term in
                           ["price", "earn", "revenue", "income", "debt", "equity",
                            "profit", "sales", "liabilit", "shareholder"]):

                        if isinstance(value, (int, float)):
                            results.append(f"{new_path}: {value}")
                        elif isinstance(value, dict):
                            # Wenn es ein dict ist, zeige die Keys
                            results.append(f"{new_path}: dict with keys: {list(value.keys())[:5]}")
                        else:
                            results.append(f"{new_path}: {value}")

                    # Rekursiv weitersuchen
                    results.extend(search_for_values(value, new_path))

            elif isinstance(obj, list):
                for i, item in enumerate(obj[:3]):  # Nur erste 3 Elemente
                    results.extend(search_for_values(item, f"{path}[{i}]"))

            return results

        # Suche in allen Daten
        found_values = search_for_values(symbol_data)

        if found_values:
            print("\n🔍 Gefundene finanzielle Werte:")
            for item in found_values[:20]:  # Zeige erste 20
                print(f"  • {item}")

            if len(found_values) > 20:
                print(f"  ... und {len(found_values) - 20} mehr")
        else:
            print("\n❌ Keine finanziellen Werte gefunden!")

            # Zeige komplette Struktur
            print("\n📋 Komplette Struktur:")
            for key, value in symbol_data.items():
                print(f"\n  {key}:")
                if isinstance(value, dict):
                    print(f"    Typ: dict")
                    print(f"    Keys: {list(value.keys())}")
                    if "fundamentals" in value:
                        fundamentals = value["fundamentals"]
                        print(f"    Fundamentals (alle Keys):")
                        for f_key, f_val in list(fundamentals.items())[:30]:
                            print(f"      - {f_key}: {f_val}")
                else:
                    print(f"    Wert: {value}")


def extract_sample_fundamentals():
    """Extrahiert Fundamentals für bessere Analyse"""
    print("\n" + "=" * 70)
    print("FUNDAMENTALS EXTRACTION")
    print("=" * 70)

    data_file = Path("data/financial_data_20251206_182246.json")

    with open(data_file, "r") as f:
        data = json.load(f)

    all_fundamentals = {}

    for symbol, symbol_data in data.items():
        print(f"\n📊 {symbol}:")

        # Sammle ALLE Fundamentals
        fundamentals_data = {}

        for key, value in symbol_data.items():
            if isinstance(value, dict) and "fundamentals" in value:
                fundamentals = value["fundamentals"]
                fundamentals_data[key] = fundamentals

        if fundamentals_data:
            # Speichere für Analyse
            all_fundamentals[symbol] = fundamentals_data

            print(f"  Fundamentals gefunden in: {list(fundamentals_data.keys())}")

            # Zeige alle Keys aus allen Fundamentals
            all_keys = set()
            for source, fund in fundamentals_data.items():
                all_keys.update(fund.keys())

            print(f"  Alle Keys ({len(all_keys)}):")
            for i, key in enumerate(sorted(all_keys)[:30], 1):
                print(f"    {i:2d}. {key}")
        else:
            print(f"  ❌ Keine Fundamentals gefunden!")

    # Speichere für spätere Analyse
    with open("data/all_fundamentals.json", "w") as f:
        json.dump(all_fundamentals, f, indent=2)

    print(f"\n✅ Alle Fundamentals gespeichert in: data/all_fundamentals.json")


if __name__ == "__main__":
    debug_data()
    extract_sample_fundamentals()