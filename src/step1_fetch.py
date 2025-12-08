# step1_fetch.py
# ----------------
# This module implements the "fetch" step (Step 1) of the ETL pipeline.
# It retrieves symbols and financial data from the Fiindo test API, filters
# symbols by target industries, maintains a local cache of known symbols,
# and writes the collected successful financial data to JSON files under `data/`.
#
# Author: Cynthia Kraft
# Date: 2025-12-08

import requests
import json
from datetime import datetime
import os
from pathlib import Path


class KnownSymbolsManager:
    """
    Manage a local cache (JSON file) of known symbols and their industries.

    Responsibilities:
    - Load the JSON file containing previously discovered symbols.
    - Save the JSON file when updated.
    - Update entries when a new symbol or industry mapping is discovered.

    The JSON file path is defined in KNOWN_SYMBOLS_FILE and is relative to the
    repository (../data/known_symbols.json).
    """

    KNOWN_SYMBOLS_FILE = "../data/known_symbols.json"

    @classmethod
    def load_known_symbols(cls) -> dict:
        """
        Load known symbols from the JSON file.

        Returns:
            dict: A mapping {symbol: industry} if file exists and is valid JSON,
                  otherwise returns an empty dict.
        """
        if Path(cls.KNOWN_SYMBOLS_FILE).exists():
            try:
                with open(cls.KNOWN_SYMBOLS_FILE, "r") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                # If the file exists but is corrupted / unreadable, warn and return empty dict.
                print(f"⚠️  Could not load {cls.KNOWN_SYMBOLS_FILE}, starting with empty dict")
                return {}
        return {}

    @classmethod
    def save_known_symbols(cls, known_symbols: dict):
        """
        Save the known symbols mapping to disk as pretty-printed JSON.

        This ensures the `data` directory exists before writing.
        """
        os.makedirs("../data", exist_ok=True)
        with open(cls.KNOWN_SYMBOLS_FILE, "w") as f:
            json.dump(known_symbols, f, indent=2, sort_keys=True)
        print(f"✅ Known symbols saved to {cls.KNOWN_SYMBOLS_FILE}")

    @classmethod
    def update_known_symbols(cls, symbol: str, industry: str):
        """
        Add or update a single symbol->industry mapping in the local cache.

        Returns:
            bool: True if the file was created or updated, False if no change was needed.
        """
        known_symbols = cls.load_known_symbols()

        if symbol not in known_symbols:
            # New symbol discovered: insert and save.
            known_symbols[symbol] = industry
            cls.save_known_symbols(known_symbols)
            print(f"  ➕ Added {symbol}: {industry} to known symbols")
            return True
        elif known_symbols.get(symbol) != industry:
            # Industry changed for an existing symbol: update and save.
            known_symbols[symbol] = industry
            cls.save_known_symbols(known_symbols)
            print(f"  🔄 Updated {symbol}: {industry} in known symbols")
            return True

        # No change needed.
        return False


class Headers():
    """
    Small helper namespace to build request headers used across the module.

    Note: Methods intentionally use simple dictionary manipulations and return
    the headers dict for easy chaining.
    """

    class General():
        @staticmethod
        def Auth(firstname, lastname, headers={}):
            """
            Add the required Authorization header. The API requires the header to be exactly:
            Authorization: Bearer {first_name}.{last_name}
            """
            headers['Authorization'] = f"Bearer {firstname}.{lastname}"
            return headers

        @staticmethod
        def Accept(headers={}):
            """
            Add an Accept header. The code uses plain text or json in different places.
            This helper sets Accept to 'text/plain' by default (some endpoints expect it).
            """
            headers['Accept'] = "text/plain"
            return headers

        @staticmethod
        def DEFAULT(firstname, lastname, headers={}):
            """
            Convenience to build a default header set (Auth + Accept).
            """
            headers = Headers.General.Auth(firstname, lastname, headers)
            headers = Headers.General.Accept(headers)
            return headers


class Fiindo_Endpoints():
    """
    Helper class grouping API endpoint URL construction and simple request wrappers.

    The API base and version are declared at the top-level of this class. Subclasses
    provide request helpers for Financials, General info, and Symbols endpoints.
    """
    api_base_url = "https://api.test.fiindo.com/api"
    api_version = "v1"

    class Financials():
        endpoint = "financials"

        # Examples of statements: 'income_statement', 'balance_sheet_statement', 'cash_flow_statement'
        @staticmethod
        def request(symbol, statement, auth_firstname, auth_lastname):
            """
            Perform a GET request to the financials endpoint for a given symbol and statement.
            Returns the raw Response object (requests.Response).
            """
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

        @staticmethod
        def income_statement(symbol, auth_firstname, auth_lastname):
            """GET income statement for a symbol."""
            return Fiindo_Endpoints.Financials.request(
                symbol,
                'income_statement',
                auth_firstname,
                auth_lastname
            )

        @staticmethod
        def balance_sheet_statement(symbol, auth_firstname, auth_lastname):
            """GET balance sheet statement for a symbol."""
            return Fiindo_Endpoints.Financials.request(
                symbol,
                'balance_sheet_statement',
                auth_firstname,
                auth_lastname
            )

        @staticmethod
        def cash_flow_statement(symbol, auth_firstname, auth_lastname):
            """GET cash flow statement for a symbol."""
            return Fiindo_Endpoints.Financials.request(
                symbol,
                'cash_flow_statement',
                auth_firstname,
                auth_lastname
            )

    class General():
        endpoint = 'general'

        @staticmethod
        def request(symbol, auth_firstname, auth_lastname):
            """
            Fetch general (profile/fundamentals) info for a symbol.
            This is used to extract the 'industry' information for filtering.
            """
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

        @staticmethod
        def request(auth_firstname, auth_lastname):
            """
            Get the list of symbols from the /symbols endpoint.
            Returns the raw Response object.
            """
            url = "/".join([
                Fiindo_Endpoints.api_base_url,
                Fiindo_Endpoints.api_version,
                Fiindo_Endpoints.Symbols.endpoint
            ])
            headers = Headers.General.DEFAULT(auth_firstname, auth_lastname)
            response_object = requests.get(url, headers=headers)
            return response_object


# -----------------------
# Configuration constants
# -----------------------
FIRST_NAME = "Cynthia"
LAST_NAME = "Kraft"
BEARER_TOKEN = f"{FIRST_NAME}.{LAST_NAME}"
API_BASE_URL = "https://api.test.fiindo.com"


def fetch_all_available_data():
    """
    Main function for Step 1: Collect all relevant financial data from the API.

    High-level process:
    1. Ensure data directory exists and load local known_symbols cache.
    2. Fetch all symbols from the API (/api/v1/symbols).
    3. For symbols not present in the local cache, request their 'general' profile to
       extract the industry and update the cache.
    4. Filter symbols to the three target industries:
         - Banks - Diversified
         - Software - Application
         - Consumer Electronics
    5. For each filtered symbol, query several endpoints (EOD, income, balance, cashflow)
       and collect data if at least 2 endpoints succeeded.
    6. Save the aggregated successful data to a timestamped JSON file under data/.
    7. Save a summary file and print a summary to stdout.

    Returns:
        dict | None: Mapping {symbol: collected_data} if any data collected, otherwise None.
    """
    print("=" * 70)
    print("STEP 1: COLLECT ALL AVAILABLE FINANCIAL DATA")
    print("=" * 70)

    # HTTP headers used for the direct requests below (Accept: application/json).
    headers = {
        "Authorization": f"Bearer {BEARER_TOKEN}",
        "Accept": "application/json"
    }

    # Ensure the output data folder exists.
    os.makedirs("../data", exist_ok=True)

    # Load local cache of previously discovered symbols.
    known_symbols = KnownSymbolsManager.load_known_symbols()
    print(f"📂 Loaded {len(known_symbols)} known symbols from file")

    # Define the industries we care about (per challenge requirements).
    target_industries = ["Banks - Diversified", "Software - Application", "Consumer Electronics"]

    # Pre-count how many known symbols belong to each target industry for reporting.
    known_in_target = {industry: 0 for industry in target_industries}
    for symbol, industry in known_symbols.items():
        if industry in target_industries:
            known_in_target[industry] = known_in_target.get(industry, 0) + 1

    print(f"📊 Known symbols in target industries:")
    for industry in target_industries:
        print(f"  • {industry}: {known_in_target.get(industry, 0)} symbols")

    all_data = {}

    # 1. Fetch the complete symbol list from the API.
    print("\n📊 Fetching all symbols from API...")
    response = requests.get(f"{API_BASE_URL}/api/v1/symbols", headers=headers)

    if response.status_code != 200:
        # If fetching the symbol list fails, the function aborts early.
        print(f"Error getting symbols: {response.status_code}")
        return

    symbols_data = response.json()
    symbols = symbols_data.get("symbols", [])
    print(f"Found {len(symbols)} total symbols in API")

    # Persist the raw symbol list for traceability.
    with open("../data/symbols.json", "w") as f:
        json.dump(symbols, f, indent=2)

    # 2. Filter symbols for our target industries. We will populate filtered_symbols.
    print("\n🔍 Filtering symbols for target industries...")
    filtered_symbols = []
    new_symbols_found = 0
    updated_symbols = 0

    for symbol in symbols:
        if symbol in known_symbols:
            # If symbol already exists in local cache, only include if in target industries.
            industry = known_symbols[symbol]
            if industry in target_industries:
                filtered_symbols.append(symbol)
            continue

        # Symbol is not in cache: fetch its general/profile endpoint to determine industry.
        try:
            print(f"  Checking {symbol}...", end="")
            response_object = Fiindo_Endpoints.General.request(
                symbol,
                FIRST_NAME,
                LAST_NAME
            )

            if response_object.status_code == 200:
                response_json = response_object.json()

                # Default industry if extraction fails.
                industry = "Unknown"
                try:
                    # Drill into the response structure to find profile -> data -> industry.
                    if "fundamentals" in response_json:
                        fundamentals = response_json["fundamentals"]
                        if "profile" in fundamentals:
                            profile = fundamentals["profile"]
                            if "data" in profile and len(profile["data"]) > 0:
                                industry = profile["data"][0].get("industry", "Unknown")
                except (KeyError, TypeError, IndexError):
                    # Any unexpected shape results in 'Unknown'
                    industry = "Unknown"

                # Update the known symbols JSON file if needed.
                if KnownSymbolsManager.update_known_symbols(symbol, industry):
                    if symbol in known_symbols:
                        updated_symbols += 1
                    else:
                        new_symbols_found += 1
                        known_symbols[symbol] = industry

                # If the symbol belongs to a target industry, add to filtered list.
                if industry in target_industries:
                    filtered_symbols.append(symbol)
                    print(f" ✅ ({industry})")
                else:
                    print(f" ❌ ({industry} - not target)")
            else:
                # Non-200 response for General endpoint.
                print(f" ❌ (API Error: {response_object.status_code})")

        except Exception as e:
            # Catch-all for network / JSON / other unexpected exceptions while checking a symbol.
            # The code intentionally prints a short error message and continues.
            print(f" ❌ (Error: {str(e)[:50]})")

    # Reload the known_symbols cache after potential updates from the loop above.
    known_symbols = KnownSymbolsManager.load_known_symbols()

    # Print a summary of the filtering step.
    print(f"\n📊 Filter Results:")
    print(f"  • Total symbols from API: {len(symbols)}")
    print(f"  • New symbols found: {new_symbols_found}")
    print(f"  • Updated symbols: {updated_symbols}")
    print(f"  • Filtered for target industries: {len(filtered_symbols)}")

    # Count how many filtered symbols belong to each target industry (based on fresh known_symbols).
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

    # 3. Collect detailed financial data for each filtered symbol.
    print(f"\n📥 Collecting financial data for {len(filtered_symbols)} symbols...")
    successful_data = {}

    for i, symbol in enumerate(filtered_symbols, 1):
        print(f"\n[{i}/{len(filtered_symbols)}] 📈 Processing {symbol}...")
        symbol_data = {}

        # Endpoints we attempt for each symbol. We try EOD (end-of-day price)
        # and three financial statements (income/balance/cashflow).
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
                # Note: uses the earlier headers variable (Accept: application/json).
                response = requests.get(f"{API_BASE_URL}{endpoint}",
                                        headers=headers, timeout=10)

                if response.status_code == 200:
                    # Only add JSON data for endpoints that returned 200.
                    symbol_data[name] = response.json()
                    endpoints_successful += 1
                    print("✅")
                else:
                    # Non-200 statuses are reported but not stored.
                    print(f"❌ {response.status_code}")
            except Exception as e:
                # Network / timeout / other exception for this endpoint is logged and skipped.
                print(f"❌ Error: {e}")

        # Heuristic: only persist symbol data when at least 2 endpoints succeeded.
        # This reduces noise / partially available data.
        if endpoints_successful >= 2:
            successful_data[symbol] = symbol_data
            print(f"  ✅ Added {symbol} to successful data ({endpoints_successful}/4 endpoints)")

    # Save the collected data if any symbol succeeded.
    if successful_data:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"data/financial_data_{timestamp}.json"

        # Write the JSON file into the repository-relative `data/` folder.
        with open(filename, "w") as f:
            json.dump(successful_data, f, indent=2)

        print(f"\n" + "=" * 70)
        print("✅ STEP 1 COMPLETED SUCCESSFULLY!")
        print("=" * 70)

        print(f"\n📊 Collected data for {len(successful_data)} symbols:")

        # Prepare summary counts per target industry based on known_symbols mapping.
        success_by_industry = {industry: 0 for industry in target_industries}
        for symbol in successful_data.keys():
            industry = known_symbols.get(symbol, "Unknown")
            if industry in target_industries:
                success_by_industry[industry] += 1

        # Print found symbols grouped by industry (for visibility).
        for industry in target_industries:
            count = success_by_industry.get(industry, 0)
            if count > 0:
                print(f"\n  {industry}: {count} symbols")
                # Show the specific symbols belonging to this industry.
                industry_symbols = [s for s in successful_data.keys()
                                    if known_symbols.get(s) == industry]
                for sym in industry_symbols:
                    print(f"    • {sym}")

        print(f"\n💾 Data saved to: {filename}")

        # Informational stats about the known symbols database.
        total_known = len(known_symbols)
        known_in_target_now = sum(1 for industry in known_symbols.values()
                                  if industry in target_industries)
        print(f"\n📋 Known symbols database:")
        print(f"  • Total known symbols: {total_known}")
        print(f"  • Known in target industries: {known_in_target_now}")
        print(f"  • File: data/known_symbols.json")

        # Save a collection summary for easy reference by later steps.
        summary = {
            "total_symbols_from_api": len(symbols),
            "filtered_symbols": len(filtered_symbols),
            "collected_symbols": len(successful_data),
            "collection_date": timestamp,
            "known_symbols_count": total_known,
            "symbols_by_industry": success_by_industry,
            "data_file": filename
        }

        with open("../data/collection_summary.json", "w") as f:
            json.dump(summary, f, indent=2)

        # Final user guidance: which script to run next.
        print(f"\n➡️  Next: Run Step 2 for calculations:")
        print(f"    python step2_calculations.py")

        # Return the successful data mapping for possible programmatic consumption.
        return successful_data
    else:
        # No data was collected successfully — inform the user and return None.
        print("\n❌ No data collected. Check API connectivity and authentication.")
        return None


if __name__ == "__main__":
    # Execute the fetch when this script is run directly.
    fetch_all_available_data()
