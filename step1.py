# step1.py

import requests
import json
from datetime import datetime
import os

# Configuration
FIRST_NAME = "Cynthia"
LAST_NAME = "Kraft"
BEARER_TOKEN = f"{FIRST_NAME}.{LAST_NAME}"
API_BASE_URL = "https://api.test.fiindo.com"


def fetch_all_available_data():
    """Fetch all data that actually works from the API"""
    print("=" * 70)
    print("STEP 1: COLLECT ALL AVAILABLE FINANCIAL DATA")
    print("=" * 70)

    headers = {
        "Authorization": f"Bearer {BEARER_TOKEN}",
        "Accept": "application/json"
    }

    # Ensure data directory exists
    os.makedirs("data", exist_ok=True)

    all_data = {}

    # 1. Get all symbols
    print("\n📊 Fetching symbols...")
    response = requests.get(f"{API_BASE_URL}/api/v1/symbols", headers=headers)

    if response.status_code != 200:
        print(f"Error getting symbols: {response.status_code}")
        return

    symbols_data = response.json()
    symbols = symbols_data.get("symbols", [])
    print(f"Found {len(symbols)} symbols")

    # Save symbols
    with open("data/symbols.json", "w") as f:
        json.dump(symbols, f, indent=2)

    # 2. For Step 1, we just need SOME financial data
    # Let's get data for first 5 symbols from the industries we're interested in
    # But since we don't have industry info yet, let's just get basic data

    print("\n💰 Collecting sample financial data...")

    # Try to find symbols that might have data
    # Let's try some well-known symbols that likely have financial data
    common_symbols = [
        "AAPL.US",  # Apple
        "MSFT.US",  # Microsoft
        "JPM.US",  # JPMorgan Chase (Bank)
        "GOOGL.US",  # Google
        "NVDA.US"  # NVIDIA
    ]

    # Filter to symbols that exist in our list
    available_common_symbols = [s for s in common_symbols if s in symbols]

    if not available_common_symbols:
        print("No common symbols found, using first 5 available symbols")
        available_common_symbols = symbols[:5]

    print(f"Testing symbols: {available_common_symbols}")

    successful_data = {}

    for symbol in available_common_symbols:
        print(f"\n📈 Processing {symbol}...")
        symbol_data = {}

        # Try each endpoint
        endpoints = [
            ("income_statement", f"/api/v1/financials/{symbol}/income_statement"),
            ("balance_sheet_statement", f"/api/v1/financials/{symbol}/balance_sheet_statement"),
            ("cash_flow_statement", f"/api/v1/financials/{symbol}/cash_flow_statement")
        ]

        for name, endpoint in endpoints:
            try:
                print(f"  • {name}: ", end="")
                response = requests.get(f"{API_BASE_URL}{endpoint}",
                                        headers=headers, timeout=10)

                if response.status_code == 200:
                    symbol_data[name] = response.json()
                    print("✅")
                else:
                    print(f"❌ {response.status_code}")
            except Exception as e:
                print(f"❌ Error: {e}")

        if symbol_data:  # If we got any data
            successful_data[symbol] = symbol_data

    # 3. Save the collected data
    if successful_data:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"data/financial_data_{timestamp}.json"

        with open(filename, "w") as f:
            json.dump(successful_data, f, indent=2)

        print(f"\n" + "=" * 70)
        print("✅ STEP 1 COMPLETED SUCCESSFULLY!")
        print("=" * 70)

        print(f"\n📊 Collected data for {len(successful_data)} symbols:")
        for symbol, data in successful_data.items():
            print(f"\n{symbol}:")
            for key in data.keys():
                print(f"  • {key}")

        print(f"\n💾 Data saved to: {filename}")
        print(f"\n➡️  Next: Analyze the data structure and proceed to calculations")

        # Also save a summary
        summary = {
            "total_symbols": len(symbols),
            "collected_symbols": list(successful_data.keys()),
            "collection_date": timestamp,
            "data_structure": {
                symbol: list(data.keys()) for symbol, data in successful_data.items()
            }
        }

        with open("data/collection_summary.json", "w") as f:
            json.dump(summary, f, indent=2)

        return successful_data
    else:
        print("\n❌ No data collected. Check API connectivity and authentication.")
        return None


if __name__ == "__main__":
    fetch_all_available_data()