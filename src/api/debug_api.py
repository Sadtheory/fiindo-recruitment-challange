# debug_api.py

import requests
import json
import sys

# Ihre Daten
FIRST_NAME = "Cynthia"
LAST_NAME = "Kraft"
BEARER_TOKEN = f"{FIRST_NAME}.{LAST_NAME}"
API_BASE_URL = "https://api.test.fiindo.com"

headers = {
    "Authorization": f"Bearer {BEARER_TOKEN}",
    "Accept": "application/json"
}


def test_endpoints():
    """Teste verschiedene API-Endpoints"""
    print("=" * 60)
    print("API ENDPOINT TESTING")
    print("=" * 60)

    # 1. Teste verschiedene Symbole
    print("\n1. Teste Symbole-Liste...")
    response = requests.get(f"{API_BASE_URL}/api/v1/symbols", headers=headers)
    if response.status_code == 200:
        symbols = response.json().get("symbols", [])
        print(f"   ✅ {len(symbols)} Symbole gefunden")
        test_symbols = symbols[:5]
        print(f"   Test-Symbole: {test_symbols}")
    else:
        print(f"   ❌ Fehler: {response.status_code}")
        return

    # 2. Teste jeden Endpunkt für jedes Test-Symbol
    for i, symbol in enumerate(test_symbols, 1):
        print(f"\n{'=' * 40}")
        print(f"Testing Symbol {i}: {symbol}")
        print(f"{'=' * 40}")

        # Test general endpoint
        print(f"\n   a) General endpoint...")
        response = requests.get(f"{API_BASE_URL}/api/v1/general/{symbol}", headers=headers)
        print(f"      Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"      Keys: {list(data.keys())}")
            if "fundamentals" in data:
                print(f"      Fundamentals Type: {type(data['fundamentals'])}")
        else:
            print(f"      Error: {response.text[:100]}")

        # Test eod endpoint
        print(f"\n   b) EOD endpoint...")
        response = requests.get(f"{API_BASE_URL}/api/v1/eod/{symbol}", headers=headers)
        print(f"      Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"      Keys: {list(data.keys())}")
        else:
            print(f"      Error: {response.text[:100]}")

        # Test debug endpoint
        print(f"\n   c) Debug endpoint...")
        response = requests.get(f"{API_BASE_URL}/api/v1/debug/{symbol}", headers=headers)
        print(f"      Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"      Keys: {list(data.keys())}")
        else:
            print(f"      Error: {response.text[:100]}")

        # Test verschiedene Financials-Typen
        print(f"\n   d) Financials endpoints testen...")

        # Mögliche statement-Typen
        statement_types = [
            "income", "balance", "cashflow", "ratios",
            "income_statement", "balance_sheet", "cash_flow",
            "all", "annual", "quarterly", "statements"
        ]

        for stmt in statement_types:
            print(f"\n      Testing: {stmt}")
            response = requests.get(f"{API_BASE_URL}/api/v1/financials/{symbol}/{stmt}",
                                    headers=headers, timeout=10)
            print(f"      Status: {response.status_code}")

            if response.status_code == 200:
                print(f"      ✅ Erfolg!")
                data = response.json()
                print(f"      Response Type: {type(data)}")
                if isinstance(data, dict):
                    print(f"      Keys: {list(data.keys())[:10]}")  # Erste 10 Keys
                elif isinstance(data, list):
                    print(f"      List length: {len(data)}")
                break  # Erfolg gefunden
            elif response.status_code != 500:  # Nicht 500, aber auch nicht 200
                print(f"      Response: {response.text[:200]}")
                break


if __name__ == "__main__":
    try:
        test_endpoints()
    except Exception as e:
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()