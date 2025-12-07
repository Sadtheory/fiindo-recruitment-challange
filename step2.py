# step2_calculations.py

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

        def search_quarterly_data(data, depth=0):
            if depth > 10:
                return None

            if isinstance(data, dict):
                # Suche nach income_statement data
                if "financials" in data and "income_statement" in data["financials"]:
                    income_stmt = data["financials"]["income_statement"]
                    if "data" in income_stmt and isinstance(income_stmt["data"], list):
                        quarters = []

                        # Gehe durch alle Einträge und identifiziere Quartale
                        for item in income_stmt["data"]:
                            if isinstance(item, dict):
                                # Prüfe ob es ein Quartal ist
                                period = item.get("period", "").lower()
                                date = item.get("date", "")

                                # Quartal erkennen: "quarter", "q", oder Datum im Quartalsformat
                                is_quarter = ("quarter" in period or
                                              "q" in period or
                                              (
                                                          len(date) == 10 and "-03-" not in date and "-06-" not in date and "-09-" not in date and "-12-" not in date))

                                if is_quarter:
                                    quarters.append(item)

                        # Finde das neueste Quartal (höchstes Datum)
                        if quarters:
                            # Sortiere nach Datum (neueste zuerst)
                            sorted_quarters = sorted(
                                quarters,
                                key=lambda x: x.get("date", ""),
                                reverse=True
                            )
                            return sorted_quarters[0]

                # Rekursiv suchen
                for value in data.values():
                    if isinstance(value, (dict, list)):
                        result = search_quarterly_data(value, depth + 1)
                        if result:
                            return result

            elif isinstance(data, list):
                for item in data:
                    result = search_quarterly_data(item, depth + 1)
                    if result:
                        return result

            return None

        return search_quarterly_data(income_data["fundamentals"])

    @staticmethod
    def find_previous_quarter(income_data: Dict, latest_quarter_date: str) -> Optional[Dict]:
        """Findet das vorherige Quartal zum gegebenen Datum"""
        if not income_data or "fundamentals" not in income_data:
            return None

        def search_previous_quarter_data(data, depth=0):
            if depth > 10:
                return None

            if isinstance(data, dict):
                if "financials" in data and "income_statement" in data["financials"]:
                    income_stmt = data["financials"]["income_statement"]
                    if "data" in income_stmt and isinstance(income_stmt["data"], list):
                        quarters = []

                        # Sammle alle Quartale
                        for item in income_stmt["data"]:
                            if isinstance(item, dict):
                                period = item.get("period", "").lower()
                                date = item.get("date", "")

                                is_quarter = ("quarter" in period or
                                              "q" in period or
                                              (
                                                          len(date) == 10 and "-03-" not in date and "-06-" not in date and "-09-" not in date and "-12-" not in date))

                                if is_quarter and date != latest_quarter_date:
                                    quarters.append(item)

                        # Sortiere nach Datum und finde das Quartal vor dem neuesten
                        if quarters:
                            sorted_quarters = sorted(
                                quarters,
                                key=lambda x: x.get("date", ""),
                                reverse=True
                            )

                            # Suche das Quartal direkt vor dem neuesten
                            for quarter in sorted_quarters:
                                if quarter.get("date", "") < latest_quarter_date:
                                    return quarter

                # Rekursiv suchen
                for value in data.values():
                    if isinstance(value, (dict, list)):
                        result = search_previous_quarter_data(value, depth + 1)
                        if result:
                            return result

            elif isinstance(data, list):
                for item in data:
                    result = search_previous_quarter_data(item, depth + 1)
                    if result:
                        return result

            return None

        return search_previous_quarter_data(income_data["fundamentals"])

    @staticmethod
    def extract_last_quarter_financials(income_data: Dict) -> Tuple[Optional[float], Optional[float]]:
        """Extrahiert Revenue und Net Income für das neueste Quartal"""
        revenue = None
        net_income = None

        latest_quarter = DataCalculator.find_latest_quarter(income_data)

        if latest_quarter:
            if "revenue" in latest_quarter and isinstance(latest_quarter["revenue"], (int, float)):
                revenue = float(latest_quarter["revenue"])

            if "netIncome" in latest_quarter and isinstance(latest_quarter["netIncome"], (int, float)):
                net_income = float(latest_quarter["netIncome"])

        return revenue, net_income

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

        def search_annual_balance_data(data, depth=0):
            if depth > 10:
                return None

            if isinstance(data, dict):
                if "financials" in data and "balance_sheet_statement" in data["financials"]:
                    balance_stmt = data["financials"]["balance_sheet_statement"]
                    if "data" in balance_stmt and isinstance(balance_stmt["data"], list):
                        annual_data = []

                        # Sammle Jahresdaten
                        for item in balance_stmt["data"]:
                            if isinstance(item, dict):
                                period = item.get("period", "").lower()
                                date = item.get("date", "")

                                # Jahresdaten erkennen
                                is_annual = ("annual" in period or
                                             "year" in period or
                                             (len(date) == 10 and (
                                                         "-12-" in date or "-03-" in date or "-06-" in date or "-09-" in date)))

                                if is_annual:
                                    annual_data.append(item)

                        # Finde neueste Jahresdaten
                        if annual_data:
                            sorted_annual = sorted(
                                annual_data,
                                key=lambda x: x.get("date", ""),
                                reverse=True
                            )
                            return sorted_annual[0]

                # Rekursiv suchen
                for value in data.values():
                    if isinstance(value, (dict, list)):
                        result = search_annual_balance_data(value, depth + 1)
                        if result:
                            return result

            elif isinstance(data, list):
                for item in data:
                    result = search_annual_balance_data(item, depth + 1)
                    if result:
                        return result

            return None

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
    def extract_net_income_ttm(income_data: Dict) -> Optional[float]:
        """Extrahiert Net Income für die letzten 12 Monate (TTM)"""
        if not income_data or "fundamentals" not in income_data:
            return None

        def search_ttm_income(data, depth=0):
            if depth > 10:
                return None

            if isinstance(data, dict):
                # Suche nach TTM Wert
                if "ttm" in data and isinstance(data["ttm"], dict):
                    ttm_data = data["ttm"]
                    if "netIncome" in ttm_data and isinstance(ttm_data["netIncome"], (int, float)):
                        return float(ttm_data["netIncome"])

                # Suche nach Net Income der letzten 4 Quartale
                if "financials" in data and "income_statement" in data["financials"]:
                    income_stmt = data["financials"]["income_statement"]
                    if "data" in income_stmt and isinstance(income_stmt["data"], list):
                        # Sammle alle Quartale
                        quarters = []
                        for item in income_stmt["data"]:
                            if isinstance(item, dict):
                                period = item.get("period", "").lower()
                                if "quarter" in period or "q" in period:
                                    if "netIncome" in item and isinstance(item["netIncome"], (int, float)):
                                        quarters.append({
                                            "date": item.get("date", ""),
                                            "netIncome": float(item["netIncome"])
                                        })

                        # Sortiere nach Datum (neueste zuerst) und summiere die letzten 4
                        if quarters:
                            sorted_quarters = sorted(
                                quarters,
                                key=lambda x: x["date"],
                                reverse=True
                            )

                            ttm_sum = 0
                            count = 0
                            for q in sorted_quarters[:4]:  # Letzte 4 Quartale
                                ttm_sum += q["netIncome"]
                                count += 1

                            if count > 0:
                                return ttm_sum

                # Rekursiv suchen
                for value in data.values():
                    if isinstance(value, (dict, list)):
                        result = search_ttm_income(value, depth + 1)
                        if result:
                            return result

            elif isinstance(data, list):
                for item in data:
                    result = search_ttm_income(item, depth + 1)
                    if result:
                        return result

            return None

        return search_ttm_income(income_data["fundamentals"])

    @staticmethod
    def extract_annual_net_income(income_data: Dict) -> Optional[float]:
        """Extrahiert jährliches Net Income für PE Ratio Berechnung"""
        if not income_data or "fundamentals" not in income_data:
            return None

        def search_annual_income(data, depth=0):
            if depth > 10:
                return None

            if isinstance(data, dict):
                # Suche nach Jahresdaten
                period = data.get("period", "").lower()
                if "annual" in period or "year" in period:
                    if "netIncome" in data and isinstance(data["netIncome"], (int, float)):
                        return float(data["netIncome"])

                if "financials" in data and "income_statement" in data["financials"]:
                    income_stmt = data["financials"]["income_statement"]
                    if "annual" in income_stmt and isinstance(income_stmt["annual"], dict):
                        annual_data = income_stmt["annual"]
                        if "netIncome" in annual_data and isinstance(annual_data["netIncome"], (int, float)):
                            return float(annual_data["netIncome"])

                # Rekursiv suchen
                for value in data.values():
                    if isinstance(value, (dict, list)):
                        result = search_annual_income(value, depth + 1)
                        if result:
                            return result

            elif isinstance(data, list):
                for item in data:
                    result = search_annual_income(item, depth + 1)
                    if result:
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


def main():
    """Hauptfunktion für Berechnungen gemäß Spezifikation"""
    print("=" * 80)
    print("STEP 2: DATA CALCULATIONS (CORRECTED - FIND LATEST QUARTER)")
    print("=" * 80)

    # Daten laden
    data_file = Path("data/financial_data_20251206_193445.json")

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

        # 2. LAST QUARTER Financials extrahieren (neuestes Quartal)
        last_quarter_revenue, last_quarter_net_income = None, None
        if "income_statement" in symbol_data:
            last_quarter_revenue, last_quarter_net_income = calculator.extract_last_quarter_financials(
                symbol_data["income_statement"])

        if last_quarter_revenue is not None:
            print(f"Last Quarter Revenue: ${last_quarter_revenue:,.0f}")
        else:
            print("Last Quarter Revenue: Not available")

        if last_quarter_net_income is not None:
            print(f"Last Quarter Net Income: ${last_quarter_net_income:,.0f}")
        else:
            print("Last Quarter Net Income: Not available")

        # 3. ANNUAL Net Income extrahieren (für PE Ratio)
        annual_net_income = None
        if "income_statement" in symbol_data:
            annual_net_income = calculator.extract_annual_net_income(symbol_data["income_statement"])

        if annual_net_income is not None:
            print(f"Annual Net Income: ${annual_net_income:,.0f}")

        # 4. Revenue Growth berechnen (Q-1 vs Q-2)
        revenue_q2, revenue_q1 = None, None
        if "income_statement" in symbol_data:
            revenue_q2, revenue_q1 = calculator.extract_revenue_for_growth_calculation(symbol_data["income_statement"])

        if revenue_q1 is not None:
            print(f"Previous Quarter Revenue (Q-1): ${revenue_q1:,.0f}")
        if revenue_q2 is not None:
            print(f"Current Quarter Revenue (Q-2): ${revenue_q2:,.0f}")

        # 5. LAST YEAR Debt & Equity für Debt Ratio
        debt, equity = None, None
        if "balance_sheet_statement" in symbol_data:
            debt, equity = calculator.extract_last_year_debt_equity(symbol_data["balance_sheet_statement"])

        if debt is not None:
            print(f"Total Debt (last year): ${debt:,.0f}")
        if equity is not None:
            print(f"Total Equity (last year): ${equity:,.0f}")

        # 6. TTM Net Income
        net_income_ttm = None
        if "income_statement" in symbol_data:
            net_income_ttm = calculator.extract_net_income_ttm(symbol_data["income_statement"])

        if net_income_ttm is not None:
            print(f"Net Income TTM: ${net_income_ttm:,.0f}")

        # Berechnungen nach Spezifikation
        print("\n📈 CALCULATED METRICS:")

        # 1. PE Ratio: Price-to-Earnings ratio
        # Verwende annual net income für PE Ratio (Standard)
        pe_ratio = None
        if latest_price and annual_net_income and annual_net_income != 0:
            pe_ratio = latest_price / annual_net_income
            print(f"PE Ratio: ${latest_price:.2f} / ${annual_net_income:,.0f} = {pe_ratio:.2f}")
        elif latest_price and last_quarter_net_income and last_quarter_net_income != 0:
            # Fallback: Quartals-Net Income × 4 für annualisierte Schätzung
            annualized_net_income = last_quarter_net_income * 4
            if annualized_net_income > 0:
                pe_ratio = latest_price / annualized_net_income
                print(
                    f"PE Ratio (estimated): ${latest_price:.2f} / (${last_quarter_net_income:,.0f} × 4) = {pe_ratio:.2f}")

        # 2. Revenue Growth: Quarter-over-quarter revenue growth (Q-1 vs Q-2)
        revenue_growth = None
        if revenue_q1 and revenue_q2 and revenue_q1 != 0:
            revenue_growth = ((revenue_q2 - revenue_q1) / revenue_q1) * 100
            print(
                f"Revenue Growth: (${revenue_q2:,.0f} - ${revenue_q1:,.0f}) / ${revenue_q1:,.0f} × 100 = {revenue_growth:.2f}%")

        # 3. NetIncomeTTM: Bereits extrahiert
        # Verwende extrahierten TTM Wert oder annual Net Income

        # 4. DebtRatio: Debt-to-equity ratio from last year
        debt_ratio = None
        if debt and equity and equity != 0:
            debt_ratio = debt / equity
            print(f"Debt Ratio: ${debt:,.0f} / ${equity:,.0f} = {debt_ratio:.4f}")

        print(f"\n✅ FINAL STATISTICS FOR {symbol}:")
        print(f"   • Latest Price: ${latest_price:,.2f}" if latest_price else "   • Price: Not available")
        print(
            f"   • Last Quarter Revenue: ${last_quarter_revenue:,.0f}" if last_quarter_revenue else "   • Revenue: Not available")
        print(f"   • PE Ratio: {pe_ratio:.2f}" if pe_ratio else "   • PE Ratio: Not available")
        print(
            f"   • Revenue Growth: {revenue_growth:.2f}%" if revenue_growth is not None else "   • Revenue Growth: Not available")
        print(
            f"   • Net Income TTM: ${net_income_ttm:,.0f}" if net_income_ttm else "   • Net Income TTM: Not available")
        print(f"   • Debt Ratio: {debt_ratio:.4f}" if debt_ratio else "   • Debt Ratio: Not available")

        # TickerStatistics erstellen
        stats = TickerStatistics(
            symbol=symbol,
            industry=industry,
            pe_ratio=pe_ratio,
            revenue_growth=revenue_growth,
            net_income_ttm=net_income_ttm,
            debt_ratio=debt_ratio,
            revenue=last_quarter_revenue,
            price=latest_price
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

        # 1. Average PE Ratio: Mean PE ratio across all tickers in each industry
        pe_ratios = [s.pe_ratio for s in stats_list if s.pe_ratio is not None]
        avg_pe = statistics.mean(pe_ratios) if pe_ratios else None

        # 2. Average Revenue Growth: Mean revenue growth across all tickers in each industry
        revenue_growths = [s.revenue_growth for s in stats_list if s.revenue_growth is not None]
        avg_revenue_growth = statistics.mean(revenue_growths) if revenue_growths else None

        # 3. Sum of Revenue: Sum revenue across all tickers in each industry
        revenues = [s.revenue for s in stats_list if s.revenue is not None]
        sum_revenue = sum(revenues) if revenues else None

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
            "net_income_ttm": stats.net_income_ttm,
            "debt_ratio": stats.debt_ratio,
            "revenue": stats.revenue,
            "price": stats.price,
            "calculation_notes": {
                "pe_ratio": "Price-to-Earnings ratio (using annual net income or estimated from quarterly)",
                "revenue_growth": "Quarter-over-quarter revenue growth (previous vs latest quarter)",
                "net_income_ttm": "Trailing twelve months net income",
                "debt_ratio": "Debt-to-equity ratio from latest year",
                "price_source": "Latest available price from stockprice.data[-1]",
                "quarter_selection": "Finds latest quarter by date, not by array position"
            }
        })

    ticker_filename = f"data/ticker_statistics_{timestamp}.json"
    with open(ticker_filename, "w") as f:
        json.dump(ticker_results, f, indent=2)
    print(f"✅ Ticker Statistics: {ticker_filename}")
    print(f"   Contains {len(ticker_results)} tickers from target industries")

    # Industry Aggregation
    industry_results_dict = []
    for agg in industry_results:
        industry_results_dict.append({
            "industry": agg.industry,
            "avg_pe_ratio": agg.avg_pe_ratio,
            "avg_revenue_growth": agg.avg_revenue_growth,
            "sum_revenue": agg.sum_revenue,
            "ticker_count": agg.ticker_count,
            "aggregation_notes": {
                "avg_pe_ratio": "Mean PE ratio across all tickers in each industry",
                "avg_revenue_growth": "Mean revenue growth across all tickers in each industry",
                "sum_revenue": "Sum revenue across all tickers in each industry"
            }
        })

    industry_filename = f"data/industry_aggregation_{timestamp}.json"
    with open(industry_filename, "w") as f:
        json.dump(industry_results_dict, f, indent=2)
    print(f"✅ Industry Aggregation: {industry_filename}")
    print(f"   Contains {len(industry_results_dict)} industries")

    # Zusammenfassung
    print("\n" + "=" * 80)
    print("✅ STEP 2 COMPLETED!")
    print("=" * 80)

    print(f"\n📊 RESULTS SUMMARY (Target Industries Only):")
    print(f"Total tickers analyzed: {len(filtered_stats)}")

    for agg in industry_results:
        print(f"\n  {agg.industry}:")
        print(f"    • Ticker Count: {agg.ticker_count}")
        if agg.avg_pe_ratio:
            print(f"    • Avg PE Ratio: {agg.avg_pe_ratio:.2f}")
        if agg.avg_revenue_growth is not None:
            print(f"    • Avg Revenue Growth: {agg.avg_revenue_growth:.2f}%")
        if agg.sum_revenue:
            print(f"    • Sum Revenue: ${agg.sum_revenue:,.0f}")

    print(f"\n📁 OUTPUT FILES:")
    print(f"   1. {ticker_filename} - Ticker statistics (filtered)")
    print(f"   2. {industry_filename} - Industry aggregations")

    print(f"\n📋 CALCULATION SPECIFICATIONS:")
    print(f"   1. PE Ratio: Latest Price / Annual Net Income (or estimated from quarterly)")
    print(f"   2. Revenue Growth: (Latest Quarter Revenue - Previous Quarter Revenue) / Previous Quarter Revenue")
    print(f"   3. Net Income TTM: Trailing Twelve Months Net Income")
    print(f"   4. Debt Ratio: Total Debt / Total Equity (from latest year)")
    print(f"   5. Quarter Selection: Finds latest quarter by date, not by array position")
    print(f"   6. Industries: {', '.join(target_industries)}")

    print(f"\n➡️  NEXT: Run Step 3 to store in database:")
    print(f"    python step3_data_storage.py")


if __name__ == "__main__":
    main()