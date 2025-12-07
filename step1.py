# step1.py

import requests
import json
from datetime import datetime
import os
from pathlib import Path


class KnownSymbolsManager:
    """Verwaltet bekannte Symbole in einer JSON-Datei"""

    KNOWN_SYMBOLS_FILE = "data/known_symbols.json"

    @classmethod
    def load_known_symbols(cls) -> dict:
        """Lädt bekannte Symbole aus JSON-Datei"""
        if Path(cls.KNOWN_SYMBOLS_FILE).exists():
            try:
                with open(cls.KNOWN_SYMBOLS_FILE, "r") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                print(f"⚠️  Could not load {cls.KNOWN_SYMBOLS_FILE}, starting with empty dict")
                return {}
        return {}

    @classmethod
    def save_known_symbols(cls, known_symbols: dict):
        """Speichert bekannte Symbole in JSON-Datei"""
        os.makedirs("data", exist_ok=True)
        with open(cls.KNOWN_SYMBOLS_FILE, "w") as f:
            json.dump(known_symbols, f, indent=2, sort_keys=True)
        print(f"✅ Known symbols saved to {cls.KNOWN_SYMBOLS_FILE}")

    @classmethod
    def update_known_symbols(cls, symbol: str, industry: str):
        """Fügt ein neues Symbol zur bekannten Liste hinzu"""
        known_symbols = cls.load_known_symbols()

        if symbol not in known_symbols:
            known_symbols[symbol] = industry
            cls.save_known_symbols(known_symbols)
            print(f"  ➕ Added {symbol}: {industry} to known symbols")
            return True
        elif known_symbols.get(symbol) != industry:
            known_symbols[symbol] = industry
            cls.save_known_symbols(known_symbols)
            print(f"  🔄 Updated {symbol}: {industry} in known symbols")
            return True

        return False


class Headers():
    class General():
        def Auth(firstname, lastname, headers={}):
            headers['Authorization'] = f"Bearer {firstname}.{lastname}"
            return headers

        def Accept(headers={}):
            headers['Accept'] = "text/plain"
            return headers

        def DEFAULT(firstname, lastname, headers={}):
            headers = Headers.General.Auth(firstname, lastname, headers)
            headers = Headers.General.Accept(headers)
            return headers


class Fiindo_Endpoints():
    api_base_url = "https://api.test.fiindo.com/api"
    api_version = "v1"

    class Financials():
        endpoint = "financials"

        # symbol = <Stock_symbol>.<Exchange_code>
        # statement = one of [
        #   'income_statement',
        #   'balance_sheet_statement',
        #   'cash_flow_statement'
        # ]
        def request(symbol, statement, auth_firstname, auth_lastname):
            url = "/".join([
                Fiindo_Endpoints.api_base_url,
                Fiindo_Endpoints.api_version,
                Fiindo_Endpoints.Financials.endpoint,
                symbol,
                statement
            ])
            headers = Headers.General.Auth(auth_firstname, auth_lastname)
            headers = Headers.General.Accept(headers)
            response_object = requests.get(url, headers=headers)
            return response_object

        def income_statement(symbol, auth_firstname, auth_lastname):
            return Fiindo_Endpoints.Financials.request(
                symbol,
                'income_statement',
                auth_firstname,
                auth_lastname
            )

        def balance_sheet_statement(symbol, auth_firstname, auth_lastname):
            return Fiindo_Endpoints.Financials.request(
                symbol,
                'balance_sheet_statement',
                auth_firstname,
                auth_lastname
            )

        def cash_flow_statement(symbol, auth_firstname, auth_lastname):
            return Fiindo_Endpoints.Financials.request(
                symbol,
                'cash_flow_statement',
                auth_firstname,
                auth_lastname
            )

    class General():
        endpoint = 'general'

        def request(symbol, auth_firstname, auth_lastname):
            url = "/".join([
                Fiindo_Endpoints.api_base_url,
                Fiindo_Endpoints.api_version,
                Fiindo_Endpoints.General.endpoint,
                symbol
            ])
            headers = Headers.General.DEFAULT(auth_firstname, auth_lastname)
            response_object = requests.get(url, headers=headers)
            return response_object

    class Symbols():
        endpoint = 'symbols'

        def request(auth_firstname, auth_lastname):
            url = "/".join([
                Fiindo_Endpoints.api_base_url,
                Fiindo_Endpoints.api_version,
                Fiindo_Endpoints.Symbols.endpoint
            ])
            headers = Headers.General.DEFAULT(auth_firstname, auth_lastname)
            response_object = requests.get(url, headers=headers)
            return response_object


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

    # Load known symbols from JSON file
    known_symbols = KnownSymbolsManager.load_known_symbols()
    print(f"📂 Loaded {len(known_symbols)} known symbols from file")

    # Count symbols by target industry
    target_industries = ["Banks - Diversified", "Software - Application", "Consumer Electronics"]
    known_in_target = {industry: 0 for industry in target_industries}

    for symbol, industry in known_symbols.items():
        if industry in target_industries:
            known_in_target[industry] = known_in_target.get(industry, 0) + 1

    print(f"📊 Known symbols in target industries:")
    for industry in target_industries:
        print(f"  • {industry}: {known_in_target.get(industry, 0)} symbols")

    all_data = {}

    # 1. Get all symbols
    print("\n📊 Fetching all symbols from API...")
    response = requests.get(f"{API_BASE_URL}/api/v1/symbols", headers=headers)

    if response.status_code != 200:
        print(f"Error getting symbols: {response.status_code}")
        return

    symbols_data = response.json()
    symbols = symbols_data.get("symbols", [])
    print(f"Found {len(symbols)} total symbols in API")

    # Save symbols
    with open("data/symbols.json", "w") as f:
        json.dump(symbols, f, indent=2)

    # Filter symbols for target industries
    print("\n🔍 Filtering symbols for target industries...")
    filtered_symbols = []
    new_symbols_found = 0
    updated_symbols = 0

    for symbol in symbols:
        if symbol in known_symbols:
            # Symbol ist bereits bekannt
            industry = known_symbols[symbol]
            if industry in target_industries:
                filtered_symbols.append(symbol)
            continue

        # Symbol ist neu, muss abgefragt werden
        try:
            print(f"  Checking {symbol}...", end="")
            response_object = Fiindo_Endpoints.General.request(
                symbol,
                FIRST_NAME,
                LAST_NAME
            )

            if response_object.status_code == 200:
                response_json = response_object.json()

                # Extrahiere Industry
                industry = "Unknown"
                try:
                    if "fundamentals" in response_json:
                        fundamentals = response_json["fundamentals"]
                        if "profile" in fundamentals:
                            profile = fundamentals["profile"]
                            if "data" in profile and len(profile["data"]) > 0:
                                industry = profile["data"][0].get("industry", "Unknown")
                except (KeyError, TypeError, IndexError):
                    industry = "Unknown"

                # Speichere/aktualisiere in known symbols
                if KnownSymbolsManager.update_known_symbols(symbol, industry):
                    if symbol in known_symbols:
                        updated_symbols += 1
                    else:
                        new_symbols_found += 1
                        known_symbols[symbol] = industry

                # Prüfe ob es in Ziel-Industrie ist
                if industry in target_industries:
                    filtered_symbols.append(symbol)
                    print(f" ✅ ({industry})")
                else:
                    print(f" ❌ ({industry} - not target)")
            else:
                print(f" ❌ (API Error: {response_object.status_code})")

        except Exception as e:
            print(f" ❌ (Error: {str(e)[:50]})")

    # Lade known symbols neu nach Updates
    known_symbols = KnownSymbolsManager.load_known_symbols()

    print(f"\n📊 Filter Results:")
    print(f"  • Total symbols from API: {len(symbols)}")
    print(f"  • New symbols found: {new_symbols_found}")
    print(f"  • Updated symbols: {updated_symbols}")
    print(f"  • Filtered for target industries: {len(filtered_symbols)}")

    # Count filtered symbols by industry
    filtered_by_industry = {industry: 0 for industry in target_industries}
    for symbol in filtered_symbols:
        industry = known_symbols.get(symbol, "Unknown")
        if industry in target_industries:
            filtered_by_industry[industry] += 1

    print(f"\n📈 Symbols by target industry:")
    for industry in target_industries:
        count = filtered_by_industry.get(industry, 0)
        if count > 0:
            print(f"  • {industry}: {count} symbols")

    # Collect financial data for filtered symbols
    print(f"\n📥 Collecting financial data for {len(filtered_symbols)} symbols...")
    successful_data = {}

    for i, symbol in enumerate(filtered_symbols, 1):
        print(f"\n[{i}/{len(filtered_symbols)}] 📈 Processing {symbol}...")
        symbol_data = {}

        # Try each endpoint
        endpoints = [
            ("eod", f"/api/v1/eod/{symbol}"),
            ("income_statement", f"/api/v1/financials/{symbol}/income_statement"),
            ("balance_sheet_statement", f"/api/v1/financials/{symbol}/balance_sheet_statement"),
            ("cash_flow_statement", f"/api/v1/financials/{symbol}/cash_flow_statement")
        ]

        endpoints_successful = 0
        for name, endpoint in endpoints:
            try:
                print(f"  • {name}: ", end="")
                response = requests.get(f"{API_BASE_URL}{endpoint}",
                                        headers=headers, timeout=10)

                if response.status_code == 200:
                    symbol_data[name] = response.json()
                    endpoints_successful += 1
                    print("✅")
                else:
                    print(f"❌ {response.status_code}")
            except Exception as e:
                print(f"❌ Error: {e}")

        if endpoints_successful >= 2:  # Wenn mindestens 2 Endpoints erfolgreich waren
            successful_data[symbol] = symbol_data
            print(f"  ✅ Added {symbol} to successful data ({endpoints_successful}/4 endpoints)")

    # Save the collected data
    if successful_data:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"data/financial_data_{timestamp}.json"

        with open(filename, "w") as f:
            json.dump(successful_data, f, indent=2)

        print(f"\n" + "=" * 70)
        print("✅ STEP 1 COMPLETED SUCCESSFULLY!")
        print("=" * 70)

        print(f"\n📊 Collected data for {len(successful_data)} symbols:")

        # Summary by industry
        success_by_industry = {industry: 0 for industry in target_industries}
        for symbol in successful_data.keys():
            industry = known_symbols.get(symbol, "Unknown")
            if industry in target_industries:
                success_by_industry[industry] += 1

        for industry in target_industries:
            count = success_by_industry.get(industry, 0)
            if count > 0:
                print(f"\n  {industry}: {count} symbols")
                # Zeige Symbole dieser Industrie
                industry_symbols = [s for s in successful_data.keys()
                                    if known_symbols.get(s) == industry]
                for sym in industry_symbols:
                    print(f"    • {sym}")

        print(f"\n💾 Data saved to: {filename}")

        # Info about known symbols file
        total_known = len(known_symbols)
        known_in_target_now = sum(1 for industry in known_symbols.values()
                                  if industry in target_industries)
        print(f"\n📋 Known symbols database:")
        print(f"  • Total known symbols: {total_known}")
        print(f"  • Known in target industries: {known_in_target_now}")
        print(f"  • File: data/known_symbols.json")

        # Also save a summary
        summary = {
            "total_symbols_from_api": len(symbols),
            "filtered_symbols": len(filtered_symbols),
            "collected_symbols": len(successful_data),
            "collection_date": timestamp,
            "known_symbols_count": total_known,
            "symbols_by_industry": success_by_industry,
            "data_file": filename
        }

        with open("data/collection_summary.json", "w") as f:
            json.dump(summary, f, indent=2)

        print(f"\n➡️  Next: Run Step 2 for calculations:")
        print(f"    python step2_calculations.py")

        return successful_data
    else:
        print("\n❌ No data collected. Check API connectivity and authentication.")
        return None


if __name__ == "__main__":
    fetch_all_available_data()