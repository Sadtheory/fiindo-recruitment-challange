# debug_stockprice.py

import json
from pathlib import Path


def debug_stockprice_structure():
    """Debuggt die Stockprice-Struktur"""
    print("=" * 70)
    print("STOCKPRICE STRUCTURE DEBUG")
    print("=" * 70)

    data_file = Path("data/financial_data_20251206_193445.json")

    with open(data_file, "r") as f:
        data = json.load(f)

    for symbol, symbol_data in data.items():
        print(f"\n{'=' * 60}")
        print(f"SYMBOL: {symbol}")
        print(f"{'=' * 60}")

        if "eod" in symbol_data:
            eod_data = symbol_data["eod"]
            print(f"EOD keys: {list(eod_data.keys())}")

            if "stockprice" in eod_data:
                stockprice = eod_data["stockprice"]
                print(f"\n📊 STOCKPRICE TYPE: {type(stockprice)}")

                if isinstance(stockprice, dict):
                    print(f"📊 STOCKPRICE DICT CONTENT:")
                    for key, value in stockprice.items():
                        print(f"  {key}: {value} (type: {type(value)})")

                        # Wenn value selbst ein dict ist
                        if isinstance(value, dict):
                            print(f"    Sub-keys: {list(value.keys())[:5]}")
                            for sub_key, sub_val in list(value.items())[:3]:
                                print(f"      {sub_key}: {sub_val}")
                        elif isinstance(value, list):
                            print(f"    List length: {len(value)}")
                            if value:
                                print(f"    First item: {value[0]}")

                elif isinstance(stockprice, (int, float)):
                    print(f"📊 STOCKPRICE VALUE: {stockprice}")
                else:
                    print(f"📊 STOCKPRICE: {stockprice}")

            # Durchsuche ALLE Werte in eod nach Zahlen
            print(f"\n🔍 ALL NUMERIC VALUES IN EOD:")

            def find_numeric_values(obj, path=""):
                results = []

                if isinstance(obj, dict):
                    for key, value in obj.items():
                        new_path = f"{path}.{key}" if path else key

                        if isinstance(value, (int, float)):
                            results.append(f"{new_path}: {value}")
                        elif isinstance(value, dict):
                            results.extend(find_numeric_values(value, new_path))
                        elif isinstance(value, list):
                            for i, item in enumerate(value[:2]):
                                results.extend(find_numeric_values(item, f"{new_path}[{i}]"))

                elif isinstance(obj, list):
                    for i, item in enumerate(obj[:2]):
                        results.extend(find_numeric_values(item, f"{path}[{i}]"))

                return results

            numeric_values = find_numeric_values(eod_data)
            for item in numeric_values[:15]:  # Erste 15 zeigen
                print(f"  {item}")


def extract_correct_price():
    """Extrahiert den korrekten Preis aus den Daten"""
    print("\n" + "=" * 70)
    print("EXTRACT CORRECT PRICE")
    print("=" * 70)

    data_file = Path("data/financial_data_20251206_193445.json")

    with open(data_file, "r") as f:
        data = json.load(f)

    for symbol, symbol_data in data.items():
        print(f"\n🔍 {symbol}:")

        if "eod" in symbol_data:
            eod_data = symbol_data["eod"]

            # Mögliche Preis-Felder
            possible_price_paths = [
                # Direkte Pfade
                ["stockprice", "price"],
                ["stockprice", "close"],
                ["stockprice", "last"],
                ["stockprice", "value"],
                ["price"],
                ["close"],
                ["lastPrice"],
                ["last_price"],
                # Verschachtelte Pfade
                ["stockprice", "data", 0, "close"],
                ["stockprice", "data", 0, "price"],
                ["data", 0, "close"],
                ["data", 0, "price"]
            ]

            def get_value_by_path(obj, path):
                """Holt Wert basierend auf Pfad"""
                current = obj
                for key in path:
                    if isinstance(current, dict) and key in current:
                        current = current[key]
                    elif isinstance(current, list) and isinstance(key, int) and key < len(current):
                        current = current[key]
                    else:
                        return None

                if isinstance(current, (int, float)):
                    return float(current)
                return None

            # Versuche alle möglichen Pfade
            found_price = None
            for path in possible_price_paths:
                price = get_value_by_path(eod_data, path)
                if price is not None:
                    found_price = price
                    print(f"  ✅ Found price at {path}: {price}")
                    break

            if found_price is None:
                print(f"  ❌ No price found in eod data")
                # Zeige eod Struktur für manuelle Inspektion
                print(f"  eod structure: {json.dumps(eod_data, indent=2)[:500]}...")


def check_income_statement():
    """Überprüft Income Statement auf realistische Werte"""
    print("\n" + "=" * 70)
    print("INCOME STATEMENT VERIFICATION")
    print("=" * 70)

    data_file = Path("data/financial_data_20251206_193445.json")

    with open(data_file, "r") as f:
        data = json.load(f)

    for symbol, symbol_data in data.items():
        print(f"\n📊 {symbol}:")

        if "income_statement" in symbol_data:
            income_data = symbol_data["income_statement"]

            # Extrahiere revenue und netIncome
            def extract_financial_values(obj, path=""):
                results = {}

                if isinstance(obj, dict):
                    # Check for financial values
                    if "revenue" in obj and isinstance(obj["revenue"], (int, float)):
                        results["revenue"] = float(obj["revenue"])
                    if "netIncome" in obj and isinstance(obj["netIncome"], (int, float)):
                        results["netIncome"] = float(obj["netIncome"])
                    if "net_income" in obj and isinstance(obj["net_income"], (int, float)):
                        results["netIncome"] = float(obj["net_income"])

                    # Rekursiv suchen
                    for key, value in obj.items():
                        if isinstance(value, (dict, list)):
                            sub_results = extract_financial_values(value, f"{path}.{key}")
                            for k, v in sub_results.items():
                                if k not in results:
                                    results[k] = v

                elif isinstance(obj, list):
                    for i, item in enumerate(obj[:2]):
                        sub_results = extract_financial_values(item, f"{path}[{i}]")
                        for k, v in sub_results.items():
                            if k not in results:
                                results[k] = v

                return results

            values = extract_financial_values(income_data)

            if values:
                print(f"  Extracted values:")
                for key, value in values.items():
                    # Formatierung für bessere Lesbarkeit
                    if value >= 1_000_000_000:
                        formatted = f"{value / 1_000_000_000:.2f}B"
                    elif value >= 1_000_000:
                        formatted = f"{value / 1_000_000:.2f}M"
                    elif value >= 1_000:
                        formatted = f"{value / 1_000:.1f}K"
                    else:
                        formatted = f"{value:,.0f}"

                    print(f"    • {key}: {formatted} (raw: {value:,.0f})")

                    # Check if realistic
                    if key == "revenue":
                        if value < 1_000_000:  # Unter 1M Revenue für große Unternehmen?
                            print(f"      ⚠️  UNREALISTIC: Revenue too small for {symbol}")
                    elif key == "netIncome":
                        if value < 100_000:  # Unter 100K Net Income?
                            print(f"      ⚠️  UNREALISTIC: Net Income too small for {symbol}")
            else:
                print(f"  ❌ No financial values found in income_statement")

                # Zeige Struktur
                if "fundamentals" in income_data:
                    print(f"  Fundamentals keys: {list(income_data['fundamentals'].keys())}")


if __name__ == "__main__":
    debug_stockprice_structure()
    extract_correct_price()
    check_income_statement()