import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import statistics
from datetime import datetime


@dataclass
class TickerStatistics:
    symbol: str
    industry: str
    pe_ratio: Optional[float] = None
    revenue_growth: Optional[float] = None
    net_income_ttm: Optional[float] = None
    debt_ratio: Optional[float] = None
    revenue: Optional[float] = None
    price: Optional[float] = None
    eps: Optional[float] = None


@dataclass
class IndustryAggregation:
    industry: str
    avg_pe_ratio: Optional[float] = None
    avg_revenue_growth: Optional[float] = None
    sum_revenue: Optional[float] = None
    ticker_count: int = 0


class DataCalculator:
    """Calculator für die spezifizierten Berechnungen"""

    @staticmethod
    def extract_latest_price(eod_data: Dict) -> Optional[float]:
        """Extrahiert NEUESTEN Preis aus EOD Daten (letzter Eintrag in Liste)"""
        if not eod_data:
            return None

        # Preis ist in stockprice.data[LAST].close
        if "stockprice" in eod_data:
            stockprice = eod_data["stockprice"]
            if isinstance(stockprice, dict) and "data" in stockprice:
                data = stockprice["data"]
                if isinstance(data, list) and len(data) > 0:
                    # Nimm den LETZTEN (neuesten) Eintrag
                    last_item = data[-1]
                    if isinstance(last_item, dict) and "close" in last_item:
                        return float(last_item["close"])

        return None

    @staticmethod
    def find_latest_quarter(income_data: Dict) -> Optional[Dict]:
        """Findet das neueste Quartal in den Finanzdaten"""
        if not income_data or "fundamentals" not in income_data:
            return None

        def search_quarterly_data(data):
            latest_quarter = None
            latest_date = ""

            if isinstance(data, dict):
                # Suche nach income_statement data
                if "financials" in data and "income_statement" in data["financials"]:
                    income_stmt = data["financials"]["income_statement"]
                    if "data" in income_stmt and isinstance(income_stmt["data"], list):
                        # Gehe durch alle Einträge und identifiziere Quartale
                        for item in income_stmt["data"]:
                            if isinstance(item, dict):
                                # Prüfe ob es ein Quartal ist
                                period = item.get("period", "").lower()
                                date = item.get("date", "")

                                # Quartal erkennen
                                is_quarter = ("quarter" in period or
                                              "q" in period or
                                              "qtr" in period or
                                              (date and len(date) >= 7))

                                if is_quarter:
                                    # Vergleiche Datum
                                    if date > latest_date:
                                        latest_date = date
                                        latest_quarter = item

                # Rekursiv suchen in allen Unterstrukturen
                for value in data.values():
                    if isinstance(value, (dict, list)):
                        result = search_quarterly_data(value)
                        if result and result.get("date", "") > latest_date:
                            latest_quarter = result
                            latest_date = result.get("date", "")

            elif isinstance(data, list):
                for item in data:
                    result = search_quarterly_data(item)
                    if result and result.get("date", "") > latest_date:
                        latest_quarter = result
                        latest_date = result.get("date", "")

            return latest_quarter

        return search_quarterly_data(income_data["fundamentals"])

    @staticmethod
    def find_previous_quarter(income_data: Dict, latest_quarter_date: str) -> Optional[Dict]:
        """Findet das vorherige Quartal zum gegebenen Datum"""
        if not income_data or "fundamentals" not in income_data:
            return None

        def search_previous_quarter_data(data):
            previous_quarter = None
            previous_date = ""

            if isinstance(data, dict):
                if "financials" in data and "income_statement" in data["financials"]:
                    income_stmt = data["financials"]["income_statement"]
                    if "data" in income_stmt and isinstance(income_stmt["data"], list):
                        # Gehe durch alle Einträge
                        for item in income_stmt["data"]:
                            if isinstance(item, dict):
                                period = item.get("period", "").lower()
                                date = item.get("date", "")

                                is_quarter = ("quarter" in period or
                                              "q" in period or
                                              "qtr" in period or
                                              (date and len(date) >= 7))

                                # Finde Quartal, das vor dem neuesten liegt
                                if is_quarter and date and date < latest_quarter_date:
                                    if date > previous_date:
                                        previous_date = date
                                        previous_quarter = item

                # Rekursiv suchen
                for value in data.values():
                    if isinstance(value, (dict, list)):
                        result = search_previous_quarter_data(value)
                        if result and result.get("date", "") > previous_date and result.get("date",
                                                                                            "") < latest_quarter_date:
                            previous_quarter = result
                            previous_date = result.get("date", "")

            elif isinstance(data, list):
                for item in data:
                    result = search_previous_quarter_data(item)
                    if result and result.get("date", "") > previous_date and result.get("date",
                                                                                        "") < latest_quarter_date:
                        previous_quarter = result
                        previous_date = result.get("date", "")

            return previous_quarter

        return search_previous_quarter_data(income_data["fundamentals"])

    @staticmethod
    def extract_last_quarter_financials(income_data: Dict) -> Tuple[Optional[float], Optional[float], Optional[float]]:
        """Extrahiert Revenue, Net Income und EPS für das neueste Quartal"""
        revenue = None
        net_income = None
        eps = None

        latest_quarter = DataCalculator.find_latest_quarter(income_data)

        if latest_quarter:
            if "revenue" in latest_quarter and isinstance(latest_quarter["revenue"], (int, float)):
                revenue = float(latest_quarter["revenue"])

            if "netIncome" in latest_quarter and isinstance(latest_quarter["netIncome"], (int, float)):
                net_income = float(latest_quarter["netIncome"])

            # EPS Werte aus dem Quartal extrahieren
            eps_keys = ["eps", "epsdiluted", "earningsPerShare", "earningsPerShareDiluted"]
            for key in eps_keys:
                if key in latest_quarter and isinstance(latest_quarter[key], (int, float)):
                    eps_value = float(latest_quarter[key])
                    if eps_value != 0:  # Ignoriere 0-Werte
                        eps = eps_value
                        break

        return revenue, net_income, eps

    @staticmethod
    def extract_revenue_for_growth_calculation(income_data: Dict) -> Tuple[Optional[float], Optional[float]]:
        """Extrahiert Revenue für aktuelles (neuestes) und vorheriges Quartal"""
        revenue_q2 = None  # Neuestes Quartal
        revenue_q1 = None  # Vorheriges Quartal

        latest_quarter = DataCalculator.find_latest_quarter(income_data)

        if latest_quarter:
            latest_date = latest_quarter.get("date", "")

            # Revenue für neuestes Quartal
            if "revenue" in latest_quarter and isinstance(latest_quarter["revenue"], (int, float)):
                revenue_q2 = float(latest_quarter["revenue"])

            # Suche vorheriges Quartal
            previous_quarter = DataCalculator.find_previous_quarter(income_data, latest_date)

            if previous_quarter:
                if "revenue" in previous_quarter and isinstance(previous_quarter["revenue"], (int, float)):
                    revenue_q1 = float(previous_quarter["revenue"])

        return revenue_q2, revenue_q1

    @staticmethod
    def find_latest_year_balance(balance_data: Dict) -> Optional[Dict]:
        """Findet die neuesten Jahresdaten in der Bilanz"""
        if not balance_data or "fundamentals" not in balance_data:
            return None

        def search_annual_balance_data(data):
            latest_year = None
            latest_date = ""

            if isinstance(data, dict):
                if "financials" in data and "balance_sheet_statement" in data["financials"]:
                    balance_stmt = data["financials"]["balance_sheet_statement"]
                    if "data" in balance_stmt and isinstance(balance_stmt["data"], list):
                        # Gehe durch alle Einträge
                        for item in balance_stmt["data"]:
                            if isinstance(item, dict):
                                period = item.get("period", "").lower()
                                date = item.get("date", "")

                                # Jahresdaten erkennen
                                is_annual = ("annual" in period or
                                             "year" in period or
                                             "fy" in period or
                                             (date and ("-12-" in date or len(date) == 4)))

                                if is_annual and date:
                                    if date > latest_date:
                                        latest_date = date
                                        latest_year = item

                # Rekursiv suchen
                for value in data.values():
                    if isinstance(value, (dict, list)):
                        result = search_annual_balance_data(value)
                        if result and result.get("date", "") > latest_date:
                            latest_year = result
                            latest_date = result.get("date", "")

            elif isinstance(data, list):
                for item in data:
                    result = search_annual_balance_data(item)
                    if result and result.get("date", "") > latest_date:
                        latest_year = result
                        latest_date = result.get("date", "")

            return latest_year

        return search_annual_balance_data(balance_data["fundamentals"])

    @staticmethod
    def extract_last_year_debt_equity(balance_data: Dict) -> Tuple[Optional[float], Optional[float]]:
        """Extrahiert Debt und Equity für das neueste Jahr"""
        debt = None
        equity = None

        latest_year_balance = DataCalculator.find_latest_year_balance(balance_data)

        if latest_year_balance:
            if "totalDebt" in latest_year_balance and isinstance(latest_year_balance["totalDebt"], (int, float)):
                debt = float(latest_year_balance["totalDebt"])

            if "totalEquity" in latest_year_balance and isinstance(latest_year_balance["totalEquity"], (int, float)):
                equity = float(latest_year_balance["totalEquity"])

        return debt, equity

    @staticmethod
    def extract_eps_values(income_data: Dict) -> Dict[str, Optional[float]]:
        """Extrahiert verschiedene EPS Werte aus den Finanzdaten"""
        eps_data = {
            "eps_ttm": None,
            "eps_annual": None,
            "eps_quarterly": None,
            "eps_diluted": None
        }

        if not income_data or "fundamentals" not in income_data:
            return eps_data

        def search_eps(data):
            found_eps = {}

            if isinstance(data, dict):
                # EPS Schlüssel
                eps_keys = {
                    "eps": "quarterly",
                    "epsdiluted": "diluted",
                    "earningsPerShare": "quarterly",
                    "earningsPerShareDiluted": "diluted",
                    "epsTTM": "ttm",
                    "epsAnnual": "annual"
                }

                # Suche nach EPS Werten
                for key, eps_type in eps_keys.items():
                    if key in data and isinstance(data[key], (int, float)):
                        eps_value = float(data[key])
                        if eps_value != 0:
                            found_eps[eps_type] = eps_value

                # Perioden-spezifische Suche
                period = data.get("period", "").lower()

                if "ttm" in period and "eps" in data and isinstance(data["eps"], (int, float)):
                    eps_value = float(data["eps"])
                    if eps_value != 0:
                        found_eps["ttm"] = eps_value

                if "annual" in period and "eps" in data and isinstance(data["eps"], (int, float)):
                    eps_value = float(data["eps"])
                    if eps_value != 0:
                        found_eps["annual"] = eps_value

                # Rekursiv suchen
                for value in data.values():
                    if isinstance(value, (dict, list)):
                        sub_results = search_eps(value)
                        for eps_type, eps_value in sub_results.items():
                            if eps_value is not None:
                                found_eps[eps_type] = eps_value

            elif isinstance(data, list):
                for item in data:
                    sub_results = search_eps(item)
                    for eps_type, eps_value in sub_results.items():
                        if eps_value is not None and eps_type not in found_eps:
                            found_eps[eps_type] = eps_value

            return found_eps

        eps_results = search_eps(income_data["fundamentals"])

        # Zuordnung zu unserer Struktur
        if "ttm" in eps_results:
            eps_data["eps_ttm"] = eps_results["ttm"]
        if "annual" in eps_results:
            eps_data["eps_annual"] = eps_results["annual"]
        if "quarterly" in eps_results:
            eps_data["eps_quarterly"] = eps_results["quarterly"]
        if "diluted" in eps_results:
            eps_data["eps_diluted"] = eps_results["diluted"]

        return eps_data

    @staticmethod
    def extract_net_income_ttm(income_data: Dict) -> Optional[float]:
        """Extrahiert Net Income für die letzten 12 Monate (TTM)"""
        if not income_data or "fundamentals" not in income_data:
            return None

        def search_ttm_income(data):
            ttm_income = None

            if isinstance(data, dict):
                # Suche nach TTM Wert
                period = data.get("period", "").lower()

                if "ttm" in period and "netIncome" in data and isinstance(data["netIncome"], (int, float)):
                    income_value = float(data["netIncome"])
                    if income_value != 0:
                        return income_value

                # Suche in TTM Objekt
                if "ttm" in data and isinstance(data["ttm"], dict):
                    ttm_data = data["ttm"]
                    if "netIncome" in ttm_data and isinstance(ttm_data["netIncome"], (int, float)):
                        income_value = float(ttm_data["netIncome"])
                        if income_value != 0:
                            return income_value

                # Rekursiv suchen
                for value in data.values():
                    if isinstance(value, (dict, list)):
                        result = search_ttm_income(value)
                        if result is not None:
                            return result

            elif isinstance(data, list):
                for item in data:
                    result = search_ttm_income(item)
                    if result is not None:
                        return result

            return ttm_income

        return search_ttm_income(income_data["fundamentals"])

    @staticmethod
    def extract_annual_net_income(income_data: Dict) -> Optional[float]:
        """Extrahiert jährliches Net Income"""
        if not income_data or "fundamentals" not in income_data:
            return None

        def income_statement_data_newer_than_previous(income_statement_data, previous_income_statement_data):
            if previous_income_statement_data is None:
                return True
            return int(previous_income_statement_data["calendarYear"]) <= int(income_statement_data["calendarYear"])

        def get_newest_year(data_list):
            newest_year = None
            for data in data_list:
                if "period" in data and data["period"] == "FY":
                    if income_statement_data_newer_than_previous(data, newest_year):
                        newest_year = data
            if newest_year is not None:
                return newest_year["netIncome"]
            return False

        get_newest_year(income_data["fundamentals"]["financials"]["income_statement"]["data"])

        def search_annual_income(data):
            if isinstance(data, dict):
                # Suche nach Jahresdaten
                period = data.get("period", "").lower()
                if period == "FY":
                    if "netIncome" in data and isinstance(data["netIncome"], (int, float)):
                        income_value = float(data["netIncome"])
                        if income_value != 0:
                            return income_value

                if "financials" in data and "income_statement" in data["financials"]:
                    income_stmt = data["financials"]["income_statement"]
                    if "annual" in income_stmt and isinstance(income_stmt["annual"], dict):
                        annual_data = income_stmt["annual"]
                        if "netIncome" in annual_data and isinstance(annual_data["netIncome"], (int, float)):
                            income_value = float(annual_data["netIncome"])
                            if income_value != 0:
                                return income_value

                # Rekursiv suchen
                for value in data.values():
                    if isinstance(value, (dict, list)):
                        result = search_annual_income(value)
                        if result is not None:
                            return result

            elif isinstance(data, list):
                for item in data:
                    result = search_annual_income(item)
                    if result is not None:
                        return result

            return None

        return search_annual_income(income_data["fundamentals"])

    @staticmethod
    def determine_industry(symbol: str) -> str:
        """Bestimmt Industrie basierend auf Symbol"""
        symbol_upper = symbol.upper()

        if any(bank in symbol_upper for bank in ["JPM", "BAC", "C", "WFC", "GS", "MS", "DB", "UBS"]):
            return "Banks - Diversified"
        elif any(tech in symbol_upper for tech in ["AAPL", "NVDA", "AMD", "INTC", "QCOM", "GOOGL", "GOOG", "META"]):
            return "Consumer Electronics"
        elif any(software in symbol_upper for software in ["MSFT", "ORCL", "SAP", "CRM", "ADBE", "INTU", "NOW"]):
            return "Software - Application"
        else:
            return "Unknown"


def find_latest_financial_data_file(data_dir: str = "data") -> Optional[Path]:
    """Findet die neueste financial_data Datei im data-Verzeichnis"""
    data_path = Path(data_dir)

    if not data_path.exists():
        print(f"❌ Data directory not found: {data_dir}")
        return None

    # Finde alle financial_data JSON Dateien
    financial_files = list(data_path.glob("financial_data_*.json"))

    if not financial_files:
        print("❌ No financial data files found")
        return None

    # Nimm die neueste Datei (basierend auf Timestamp im Dateinamen)
    latest_file = max(financial_files, key=lambda x: x.stem)
    return latest_file


def main():
    """Hauptfunktion für Berechnungen gemäß Spezifikation"""
    print("=" * 80)
    print("STEP 2: DATA CALCULATIONS (WITH EPS SUPPORT)")
    print("=" * 80)

    # Finde neueste Daten-Datei
    data_file = find_latest_financial_data_file()

    if not data_file:
        print("❌ Could not find financial data file. Please run Step 1 first.")
        return

    print(f"📁 Using data file: {data_file.name}")

    # Daten laden
    with open(data_file, "r") as f:
        raw_data = json.load(f)

    print(f"📊 Analysiere {len(raw_data)} Symbole")

    calculator = DataCalculator()
    all_stats = []

    print("\n" + "=" * 80)
    print("CALCULATIONS PER TICKER")
    print("=" * 80)

    for symbol, symbol_data in raw_data.items():
        print(f"\n🔹 {symbol}:")
        print("-" * 40)

        # Industrie bestimmen
        industry = calculator.determine_industry(symbol)
        print(f"Industry: {industry}")

        # 1. LATEST Price extrahieren
        latest_price = None
        if "eod" in symbol_data:
            latest_price = calculator.extract_latest_price(symbol_data["eod"])

        if latest_price is not None:
            print(f"Latest Price: ${latest_price:.2f}")
        else:
            print("Latest Price: Not available")

        # 2. LAST QUARTER Financials extrahieren (mit EPS)
        last_quarter_revenue, last_quarter_net_income, last_quarter_eps = None, None, None
        if "income_statement" in symbol_data:
            last_quarter_revenue, last_quarter_net_income, last_quarter_eps = calculator.extract_last_quarter_financials(
                symbol_data["income_statement"])

        if last_quarter_revenue is not None:
            print(f"Last Quarter Revenue: ${last_quarter_revenue:,.0f}")
        else:
            print("Last Quarter Revenue: Not available")

        if last_quarter_net_income is not None:
            print(f"Last Quarter Net Income: ${last_quarter_net_income:,.0f}")
        else:
            print("Last Quarter Net Income: Not available")

        if last_quarter_eps is not None:
            print(f"Last Quarter EPS: ${last_quarter_eps:.2f}")
        else:
            print("Last Quarter EPS: Not available")

        # 3. EPS Werte extrahieren
        eps_data = {}
        if "income_statement" in symbol_data:
            eps_data = calculator.extract_eps_values(symbol_data["income_statement"])

            if eps_data["eps_ttm"]:
                print(f"EPS TTM: ${eps_data['eps_ttm']:.2f}")
            if eps_data["eps_annual"]:
                print(f"EPS Annual: ${eps_data['eps_annual']:.2f}")
            if eps_data["eps_quarterly"]:
                print(f"EPS Quarterly: ${eps_data['eps_quarterly']:.2f}")

        # 4. ANNUAL Net Income extrahieren
        annual_net_income = None
        if "income_statement" in symbol_data:
            annual_net_income = calculator.extract_annual_net_income(symbol_data["income_statement"])

        if annual_net_income is not None:
            print(f"Annual Net Income: ${annual_net_income:,.0f}")

        # 5. Revenue Growth berechnen
        revenue_q2, revenue_q1 = None, None
        if "income_statement" in symbol_data:
            revenue_q2, revenue_q1 = calculator.extract_revenue_for_growth_calculation(symbol_data["income_statement"])

        if revenue_q1 is not None:
            print(f"Previous Quarter Revenue (Q-1): ${revenue_q1:,.0f}")
        if revenue_q2 is not None:
            print(f"Current Quarter Revenue (Q-2): ${revenue_q2:,.0f}")

        # 6. LAST YEAR Debt & Equity
        debt, equity = None, None
        if "balance_sheet_statement" in symbol_data:
            debt, equity = calculator.extract_last_year_debt_equity(symbol_data["balance_sheet_statement"])

        if debt is not None:
            print(f"Total Debt (last year): ${debt:,.0f}")
        if equity is not None:
            print(f"Total Equity (last year): ${equity:,.0f}")

        # 7. TTM Net Income (WICHTIG: muss in die Aggregation!)
        net_income_ttm = None
        if "income_statement" in symbol_data:
            net_income_ttm = calculator.extract_net_income_ttm(symbol_data["income_statement"])

        if net_income_ttm is not None:
            print(f"Net Income TTM: ${net_income_ttm:,.0f}")

        # Berechnungen nach Spezifikation
        print("\n📈 CALCULATED METRICS:")

        # 1. PE Ratio: Price-to-Earnings ratio (mit EPS)
        pe_ratio = None
        eps_for_pe = None

        # 1. PE Ratio: Price-to-Earnings ratio (mit EPS)
        pe_ratio = None
        eps_for_pe = None

        # Priorität 1: EPS TTM verwenden (sicherer Zugriff mit .get())
        if latest_price and eps_data.get("eps_ttm") and eps_data["eps_ttm"] != 0:
            eps_for_pe = eps_data["eps_ttm"]
            pe_ratio = latest_price / eps_for_pe
            print(f"PE Ratio (using EPS TTM): ${latest_price:.2f} / ${eps_for_pe:.2f} = {pe_ratio:.2f}")

        # Priorität 2: EPS Annual verwenden
        elif latest_price and eps_data.get("eps_annual") and eps_data["eps_annual"] != 0:
            eps_for_pe = eps_data["eps_annual"]
            pe_ratio = latest_price / eps_for_pe
            print(f"PE Ratio (using EPS Annual): ${latest_price:.2f} / ${eps_for_pe:.2f} = {pe_ratio:.2f}")

        # Priorität 3: Quartals-EPS × 4 für Schätzung
        elif latest_price and last_quarter_eps and last_quarter_eps != 0:
            eps_for_pe = last_quarter_eps * 4
            pe_ratio = latest_price / eps_for_pe
            print(
                f"PE Ratio (estimated from quarterly EPS): ${latest_price:.2f} / (${last_quarter_eps:.2f} × 4) = {pe_ratio:.2f}")

        # Priorität 4: Annual Net Income verwenden
        elif latest_price and annual_net_income and annual_net_income != 0:
            pe_ratio = latest_price / annual_net_income
            print(
                f"PE Ratio (using Annual Net Income): ${latest_price:.2f} / ${annual_net_income:,.0f} = {pe_ratio:.2f}")

        # 2. Revenue Growth
        revenue_growth = None
        if revenue_q1 and revenue_q2 and revenue_q1 != 0:
            revenue_growth = ((revenue_q2 - revenue_q1) / revenue_q1) * 100
            print(
                f"Revenue Growth: (${revenue_q2:,.0f} - ${revenue_q1:,.0f}) / ${revenue_q1:,.0f} × 100 = {revenue_growth:.2f}%")

        # 3. NetIncomeTTM - WICHTIG: wird bereits oben extrahiert und muss in die Statistik

        # 4. DebtRatio
        debt_ratio = None
        if debt and equity and equity != 0:
            debt_ratio = debt / equity
            print(f"Debt Ratio: ${debt:,.0f} / ${equity:,.0f} = {debt_ratio:.4f}")

        print(f"\n✅ FINAL STATISTICS FOR {symbol}:")
        print(f"   • Latest Price: ${latest_price:,.2f}" if latest_price else "   • Price: Not available")
        print(
            f"   • Last Quarter Revenue: ${last_quarter_revenue:,.0f}" if last_quarter_revenue else "   • Revenue: Not available")
        print(f"   • EPS (for PE calculation): ${eps_for_pe:.2f}" if eps_for_pe else "   • EPS: Not available")
        print(f"   • PE Ratio: {pe_ratio:.2f}" if pe_ratio else "   • PE Ratio: Not available")
        print(
            f"   • Revenue Growth: {revenue_growth:.2f}%" if revenue_growth is not None else "   • Revenue Growth: Not available")
        print(
            f"   • Net Income TTM: ${net_income_ttm:,.0f}" if net_income_ttm else "   • Net Income TTM: Not available")
        print(f"   • Debt Ratio: {debt_ratio:.4f}" if debt_ratio else "   • Debt Ratio: Not available")

        # TickerStatistics erstellen MIT net_income_ttm
        stats = TickerStatistics(
            symbol=symbol,
            industry=industry,
            pe_ratio=pe_ratio,
            revenue_growth=revenue_growth,
            net_income_ttm=net_income_ttm,  # WICHTIG: Hier wird es gespeichert
            debt_ratio=debt_ratio,
            revenue=last_quarter_revenue,
            price=latest_price,
            eps=eps_for_pe
        )

        all_stats.append(stats)

    # Nur Symbole aus den 3 gewünschten Industrien filtern
    print("\n" + "=" * 80)
    print("FILTERING FOR TARGET INDUSTRIES")
    print("=" * 80)

    target_industries = ["Banks - Diversified", "Software - Application", "Consumer Electronics"]
    filtered_stats = [stats for stats in all_stats if stats.industry in target_industries]

    print(f"Symbole vor Filterung: {len(all_stats)}")
    print(f"Symbole nach Filterung ({', '.join(target_industries)}): {len(filtered_stats)}")

    # Zeige gefilterte Symbole
    for industry in target_industries:
        industry_symbols = [s.symbol for s in filtered_stats if s.industry == industry]
        if industry_symbols:
            print(f"  {industry}: {len(industry_symbols)} Symbole - {', '.join(industry_symbols)}")

    # Industry Aggregation NUR für die 3 Ziel-Industrien
    print("\n" + "=" * 80)
    print("INDUSTRY AGGREGATION")
    print("=" * 80)

    industries = {}
    for stats in filtered_stats:
        if stats.industry not in industries:
            industries[stats.industry] = []
        industries[stats.industry].append(stats)

    industry_results = []

    for industry, stats_list in industries.items():
        print(f"\n📊 {industry} ({len(stats_list)} Ticker):")

        # Durchschnittliche PE Ratio
        pe_ratios = [s.pe_ratio for s in stats_list if s.pe_ratio is not None and s.pe_ratio != 0]
        avg_pe = statistics.mean(pe_ratios) if pe_ratios else None

        # Durchschnittliches Revenue Growth
        revenue_growths = [s.revenue_growth for s in stats_list if s.revenue_growth is not None]
        avg_revenue_growth = statistics.mean(revenue_growths) if revenue_growths else None

        # Summe der Revenues
        revenues = [s.revenue for s in stats_list if s.revenue is not None]
        sum_revenue = sum(revenues) if revenues else None

        # Summe der Net Income TTM (WICHTIG: für Aggregation)
        net_incomes_ttm = [s.net_income_ttm for s in stats_list if s.net_income_ttm is not None]
        sum_net_income_ttm = sum(net_incomes_ttm) if net_incomes_ttm else None
        avg_net_income_ttm = statistics.mean(net_incomes_ttm) if net_incomes_ttm else None

        # Zeige Null-EPS Fälle
        zero_eps_count = sum(1 for s in stats_list if s.eps == 0 or s.eps is None)
        if zero_eps_count > 0:
            print(f"   ⚠️  {zero_eps_count} Ticker haben keinen EPS Wert für PE Berechnung")

        if avg_pe is not None:
            print(f"   • Average PE Ratio: {avg_pe:.2f} (from {len(pe_ratios)} tickers)")
        else:
            print(f"   • Average PE Ratio: No data available")

        if avg_revenue_growth is not None:
            print(f"   • Average Revenue Growth: {avg_revenue_growth:.2f}% (from {len(revenue_growths)} tickers)")
        else:
            print(f"   • Average Revenue Growth: No data available")

        if sum_revenue is not None:
            print(f"   • Sum Revenue: ${sum_revenue:,.0f} (from {len(revenues)} tickers)")
        else:
            print(f"   • Sum Revenue: No data available")

        if sum_net_income_ttm is not None:
            print(f"   • Sum Net Income TTM: ${sum_net_income_ttm:,.0f} (from {len(net_incomes_ttm)} tickers)")
        if avg_net_income_ttm is not None:
            print(f"   • Average Net Income TTM: ${avg_net_income_ttm:,.0f}")

        industry_agg = IndustryAggregation(
            industry=industry,
            avg_pe_ratio=avg_pe,
            avg_revenue_growth=avg_revenue_growth,
            sum_revenue=sum_revenue,
            ticker_count=len(stats_list)
        )

        industry_results.append(industry_agg)

    # Ergebnisse speichern
    print("\n" + "=" * 80)
    print("SAVING RESULTS")
    print("=" * 80)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Ticker Statistics (nur gefilterte)
    ticker_results = []
    for stats in filtered_stats:
        ticker_results.append({
            "symbol": stats.symbol,
            "industry": stats.industry,
            "pe_ratio": stats.pe_ratio,
            "revenue_growth": stats.revenue_growth,
            "net_income_ttm": stats.net_income_ttm,  # WICHTIG: Hier enthalten
            "debt_ratio": stats.debt_ratio,
            "revenue": stats.revenue,
            "price": stats.price,
            "eps": stats.eps,
            "calculation_notes": {
                "pe_ratio": "Price-to-Earnings ratio (calculated from available EPS values)",
                "eps_source": "Priority: EPS TTM > EPS Annual > Quarterly EPS × 4 > Annual Net Income",
                "revenue_growth": "Quarter-over-quarter revenue growth (previous vs latest quarter)",
                "net_income_ttm": "Trailing twelve months net income (extracted from income statement)",
                "debt_ratio": "Debt-to-equity ratio from latest year",
                "quarter_selection": "Finds latest quarter by date"
            }
        })

    ticker_filename = f"data/ticker_statistics_{timestamp}.json"
    with open(ticker_filename, "w") as f:
        json.dump(ticker_results, f, indent=2)
    print(f"✅ Ticker Statistics: {ticker_filename}")
    print(f"   Contains {len(ticker_results)} tickers from target industries")

    # Industry Aggregation MIT Net Income TTM Informationen
    industry_results_dict = []
    for agg in industry_results:
        # Finde zusätzliche Net Income TTM Daten für diese Industrie
        industry_tickers = [s for s in filtered_stats if s.industry == agg.industry]
        net_incomes_ttm = [s.net_income_ttm for s in industry_tickers if s.net_income_ttm is not None]
        sum_net_income_ttm = sum(net_incomes_ttm) if net_incomes_ttm else None
        avg_net_income_ttm = statistics.mean(net_incomes_ttm) if net_incomes_ttm else None

        industry_result = {
            "industry": agg.industry,
            "avg_pe_ratio": agg.avg_pe_ratio,
            "avg_revenue_growth": agg.avg_revenue_growth,
            "sum_revenue": agg.sum_revenue,
            "ticker_count": agg.ticker_count,
            "net_income_ttm_stats": {  # WICHTIG: Hier hinzugefügt
                "sum_net_income_ttm": sum_net_income_ttm,
                "avg_net_income_ttm": avg_net_income_ttm,
                "tickers_with_data": len(net_incomes_ttm)
            },
            "aggregation_notes": {
                "avg_pe_ratio": "Mean PE ratio across all tickers in each industry",
                "avg_revenue_growth": "Mean revenue growth across all tickers in each industry",
                "sum_revenue": "Sum revenue across all tickers in each industry",
                "net_income_ttm": "Net Income TTM statistics included per industry"
            }
        }
        industry_results_dict.append(industry_result)

    industry_filename = f"data/industry_aggregation_{timestamp}.json"
    with open(industry_filename, "w") as f:
        json.dump(industry_results_dict, f, indent=2)
    print(f"✅ Industry Aggregation: {industry_filename}")
    print(f"   Contains {len(industry_results_dict)} industries")
    print(f"   Includes Net Income TTM statistics for each industry")

    # Zusammenfassung
    print("\n" + "=" * 80)
    print("✅ STEP 2 COMPLETED!")
    print("=" * 80)

    print(f"\n📊 RESULTS SUMMARY (Target Industries Only):")
    print(f"Total tickers analyzed: {len(filtered_stats)}")

    for agg in industry_results:
        # Zusätzliche Net Income TTM Daten für die Zusammenfassung
        industry_tickers = [s for s in filtered_stats if s.industry == agg.industry]
        net_incomes_ttm = [s.net_income_ttm for s in industry_tickers if s.net_income_ttm is not None]
        sum_net_income_ttm = sum(net_incomes_ttm) if net_incomes_ttm else None

        print(f"\n  {agg.industry}:")
        print(f"    • Ticker Count: {agg.ticker_count}")
        if agg.avg_pe_ratio:
            print(f"    • Avg PE Ratio: {agg.avg_pe_ratio:.2f}")
        if agg.avg_revenue_growth is not None:
            print(f"    • Avg Revenue Growth: {agg.avg_revenue_growth:.2f}%")
        if agg.sum_revenue:
            print(f"    • Sum Revenue: ${agg.sum_revenue:,.0f}")
        if sum_net_income_ttm:
            print(f"    • Sum Net Income TTM: ${sum_net_income_ttm:,.0f}")

    print(f"\n📁 OUTPUT FILES:")
    print(f"   1. {ticker_filename} - Ticker statistics (filtered)")
    print(f"   2. {industry_filename} - Industry aggregations")

    print(f"\n📋 CALCULATION SPECIFICATIONS:")
    print(f"   1. PE Ratio: Latest Price / EPS (TTM > Annual > Quarterly×4 > Annual Net Income)")
    print(f"   2. Revenue Growth: (Latest Quarter Revenue - Previous Quarter Revenue) / Previous Quarter Revenue")
    print(f"   3. Net Income TTM: Trailing Twelve Months Net Income (included in both ticker and industry data)")
    print(f"   4. Debt Ratio: Total Debt / Total Equity (from latest year)")
    print(f"   5. Quarter Selection: Finds latest quarter by date")
    print(f"   6. Data Source: Uses latest financial_data_*.json file")

    print(f"\n➡️  NEXT: Run Step 3 to store in database:")
    print(f"    python step3_data_storage.py")


if __name__ == "__main__":
    main()