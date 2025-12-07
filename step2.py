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
    def extract_last_quarter_financials(income_data: Dict) -> Tuple[Optional[float], Optional[float]]:
        """Extrahiert Revenue und Net Income für das letzte Quartal (data[0])"""
        revenue = None
        net_income = None

        if not income_data or "fundamentals" not in income_data:
            return revenue, net_income

        def search_last_quarter_values(data):
            nonlocal revenue, net_income

            if isinstance(data, dict):
                # In financials.income_statement.data suchen (data[0] = letztes Quartal)
                if "financials" in data and "income_statement" in data["financials"]:
                    income_stmt = data["financials"]["income_statement"]
                    if "data" in income_stmt and isinstance(income_stmt["data"], list) and len(income_stmt["data"]) > 0:
                        # LETZTES Quartal ist data[0]
                        last_quarter = income_stmt["data"][0]

                        if revenue is None and "revenue" in last_quarter and isinstance(last_quarter["revenue"],
                                                                                        (int, float)):
                            revenue = float(last_quarter["revenue"])

                        if net_income is None and "netIncome" in last_quarter and isinstance(last_quarter["netIncome"],
                                                                                             (int, float)):
                            net_income = float(last_quarter["netIncome"])

                # Allgemeine Suche als Fallback
                if revenue is None and "revenue" in data and isinstance(data["revenue"], (int, float)):
                    revenue = float(data["revenue"])

                if net_income is None and "netIncome" in data and isinstance(data["netIncome"], (int, float)):
                    net_income = float(data["netIncome"])

                # Rekursiv suchen
                for value in data.values():
                    if isinstance(value, (dict, list)):
                        search_last_quarter_values(value)

            elif isinstance(data, list):
                for item in data:
                    search_last_quarter_values(item)

        search_last_quarter_values(income_data["fundamentals"])
        return revenue, net_income

    @staticmethod
    def extract_revenue_for_growth_calculation(income_data: Dict) -> Tuple[Optional[float], Optional[float]]:
        """Extrahiert Revenue für aktuelles (Q-2) und vorheriges Quartal (Q-1) für Growth-Berechnung"""
        revenue_q2 = None  # Aktuelles Quartal (data[0])
        revenue_q1 = None  # Vorheriges Quartal (data[1])

        if not income_data or "fundamentals" not in income_data:
            return revenue_q2, revenue_q1

        fundamentals = income_data["fundamentals"]

        def search_quarterly_revenue(data):
            nonlocal revenue_q2, revenue_q1

            if isinstance(data, dict):
                if "financials" in data and "income_statement" in data["financials"]:
                    income_stmt = data["financials"]["income_statement"]
                    if "data" in income_stmt and isinstance(income_stmt["data"], list):
                        # Q-2: Letztes Quartal (data[0])
                        if len(income_stmt["data"]) > 0 and revenue_q2 is None:
                            q2_data = income_stmt["data"][0]
                            if "revenue" in q2_data and isinstance(q2_data["revenue"], (int, float)):
                                revenue_q2 = float(q2_data["revenue"])

                        # Q-1: Vorletztes Quartal (data[1])
                        if len(income_stmt["data"]) > 1 and revenue_q1 is None:
                            q1_data = income_stmt["data"][1]
                            if "revenue" in q1_data and isinstance(q1_data["revenue"], (int, float)):
                                revenue_q1 = float(q1_data["revenue"])

                # Rekursiv suchen
                for value in data.values():
                    if isinstance(value, (dict, list)):
                        search_quarterly_revenue(value)

            elif isinstance(data, list):
                for item in data:
                    search_quarterly_revenue(item)

        search_quarterly_revenue(fundamentals)
        return revenue_q2, revenue_q1

    @staticmethod
    def extract_last_year_debt_equity(balance_data: Dict) -> Tuple[Optional[float], Optional[float]]:
        """Extrahiert Debt und Equity für das letzte Jahr (data[0])"""
        debt = None
        equity = None

        if not balance_data or "fundamentals" not in balance_data:
            return debt, equity

        def search_last_year_values(data):
            nonlocal debt, equity

            if isinstance(data, dict):
                # In financials.balance_sheet_statement.data suchen (data[0] = letztes Jahr)
                if "financials" in data and "balance_sheet_statement" in data["financials"]:
                    balance_stmt = data["financials"]["balance_sheet_statement"]
                    if "data" in balance_stmt and isinstance(balance_stmt["data"], list) and len(
                            balance_stmt["data"]) > 0:
                        # LETZTES Jahr ist data[0]
                        last_year = balance_stmt["data"][0]

                        if debt is None and "totalDebt" in last_year and isinstance(last_year["totalDebt"],
                                                                                    (int, float)):
                            debt = float(last_year["totalDebt"])

                        if equity is None and "totalEquity" in last_year and isinstance(last_year["totalEquity"],
                                                                                        (int, float)):
                            equity = float(last_year["totalEquity"])

                # Allgemeine Suche als Fallback
                if debt is None and "totalDebt" in data and isinstance(data["totalDebt"], (int, float)):
                    debt = float(data["totalDebt"])

                if equity is None and "totalEquity" in data and isinstance(data["totalEquity"], (int, float)):
                    equity = float(data["totalEquity"])

                # Rekursiv suchen
                for value in data.values():
                    if isinstance(value, (dict, list)):
                        search_last_year_values(value)

            elif isinstance(data, list):
                for item in data:
                    search_last_year_values(item)

        search_last_year_values(balance_data["fundamentals"])
        return debt, equity

    @staticmethod
    def extract_net_income_ttm(income_data: Dict) -> Optional[float]:
        """Extrahiert Net Income für die letzten 12 Monate (TTM)"""
        if not income_data or "fundamentals" not in income_data:
            return None

        # Versuche TTM direkt zu finden
        def search_ttm_income(data):
            if isinstance(data, dict):
                # Suche nach TTM oder letzten 4 Quartalen
                if "netIncome" in data and isinstance(data["netIncome"], (int, float)):
                    # Falls es ein TTM Wert ist
                    return float(data["netIncome"])

                # Suche in income statement data und summiere die letzten 4 Quartale
                if "financials" in data and "income_statement" in data["financials"]:
                    income_stmt = data["financials"]["income_statement"]
                    if "data" in income_stmt and isinstance(income_stmt["data"], list):
                        # Summiere Net Income der letzten 4 Quartale
                        ttm_income = 0
                        quarters_counted = 0
                        for quarter_data in income_stmt["data"][:4]:  # Letzte 4 Quartale
                            if "netIncome" in quarter_data and isinstance(quarter_data["netIncome"], (int, float)):
                                ttm_income += float(quarter_data["netIncome"])
                                quarters_counted += 1

                        if quarters_counted > 0:
                            return ttm_income

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

            return None

        return search_ttm_income(income_data["fundamentals"])

    @staticmethod
    def determine_industry(symbol: str) -> str:
        """Bestimmt Industrie basierend auf Symbol"""
        # Erweiterte Industrieerkennung
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
    print("STEP 2: DATA CALCULATIONS")
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

        # Industrie bestimmen
        industry = calculator.determine_industry(symbol)
        print(f"   Industry: {industry}")

        # 1. LATEST Price extrahieren
        latest_price = None
        if "eod" in symbol_data:
            latest_price = calculator.extract_latest_price(symbol_data["eod"])

        if latest_price is not None:
            print(f"   Latest Price: ${latest_price:.2f}")

        # 2. LAST QUARTER Financials extrahieren
        last_quarter_revenue, last_quarter_net_income = None, None
        if "income_statement" in symbol_data:
            last_quarter_revenue, last_quarter_net_income = calculator.extract_last_quarter_financials(
                symbol_data["income_statement"])

        if last_quarter_revenue is not None:
            print(f"   Last Quarter Revenue: ${last_quarter_revenue:,.0f}")
        if last_quarter_net_income is not None:
            print(f"   Last Quarter Net Income: ${last_quarter_net_income:,.0f}")

        # 3. TTM Net Income extrahieren
        net_income_ttm = None
        if "income_statement" in symbol_data:
            net_income_ttm = calculator.extract_net_income_ttm(symbol_data["income_statement"])

        if net_income_ttm is not None:
            print(f"   Net Income TTM: ${net_income_ttm:,.0f}")

        # 4. Revenue Growth berechnen (Q-1 vs Q-2)
        revenue_q2, revenue_q1 = None, None
        if "income_statement" in symbol_data:
            revenue_q2, revenue_q1 = calculator.extract_revenue_for_growth_calculation(symbol_data["income_statement"])

        if revenue_q1 is not None:
            print(f"   Previous Quarter Revenue (Q-1): ${revenue_q1:,.0f}")
        if revenue_q2 is not None:
            print(f"   Current Quarter Revenue (Q-2): ${revenue_q2:,.0f}")

        # 5. LAST YEAR Debt & Equity für Debt Ratio
        debt, equity = None, None
        if "balance_sheet_statement" in symbol_data:
            debt, equity = calculator.extract_last_year_debt_equity(symbol_data["balance_sheet_statement"])

        if debt is not None:
            print(f"   Total Debt (last year): ${debt:,.0f}")
        if equity is not None:
            print(f"   Total Equity (last year): ${equity:,.0f}")

        # Berechnungen nach Spezifikation
        # 1. PE Ratio: Price-to-Earnings ratio from last quarter
        pe_ratio = None
        if latest_price and last_quarter_net_income and last_quarter_net_income != 0:
            pe_ratio = latest_price / last_quarter_net_income
            print(f"   PE Ratio: ${latest_price:.2f} / ${last_quarter_net_income:,.0f} = {pe_ratio:.2f}")

        # 2. Revenue Growth: Quarter-over-quarter revenue growth (Q-1 vs Q-2)
        revenue_growth = None
        if revenue_q1 and revenue_q2 and revenue_q1 != 0:
            revenue_growth = ((revenue_q2 - revenue_q1) / revenue_q1) * 100
            print(
                f"   Revenue Growth: (${revenue_q2:,.0f} - ${revenue_q1:,.0f}) / ${revenue_q1:,.0f} × 100 = {revenue_growth:.2f}%")

        # 3. NetIncomeTTM: Trailing twelve months net income (bereits extrahiert)

        # 4. DebtRatio: Debt-to-equity ratio from last year
        debt_ratio = None
        if debt and equity and equity != 0:
            debt_ratio = debt / equity
            print(f"   Debt Ratio: ${debt:,.0f} / ${equity:,.0f} = {debt_ratio:.4f}")

        print(f"\n   📊 FINAL STATISTICS FOR {symbol}:")
        print(f"     • Latest Price: ${latest_price:,.2f}" if latest_price else "     • Price: Not available")
        print(
            f"     • Last Quarter Revenue: ${last_quarter_revenue:,.0f}" if last_quarter_revenue else "     • Revenue: Not available")
        print(
            f"     • PE Ratio (based on last quarter): {pe_ratio:.2f}" if pe_ratio else "     • PE Ratio: Not available")
        print(
            f"     • Revenue Growth (QoQ): {revenue_growth:.2f}%" if revenue_growth is not None else "     • Revenue Growth: Not available")
        print(
            f"     • Net Income TTM: ${net_income_ttm:,.0f}" if net_income_ttm else "     • Net Income TTM: Not available")
        print(
            f"     • Debt Ratio (from last year): {debt_ratio:.4f}" if debt_ratio else "     • Debt Ratio: Not available")

        # TickerStatistics erstellen
        stats = TickerStatistics(
            symbol=symbol,
            industry=industry,
            pe_ratio=pe_ratio,
            revenue_growth=revenue_growth,
            net_income_ttm=net_income_ttm,
            debt_ratio=debt_ratio,
            revenue=last_quarter_revenue
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
            "calculation_notes": {
                "pe_ratio": "Price-to-Earnings ratio from last quarter",
                "revenue_growth": "Quarter-over-quarter revenue growth (Q-1 vs Q-2)",
                "net_income_ttm": "Trailing twelve months net income",
                "debt_ratio": "Debt-to-equity ratio from last year",
                "price_source": "Latest available price from stockprice.data[-1]"
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
    print(f"   1. PE Ratio: Latest Price / Last Quarter Net Income")
    print(f"   2. Revenue Growth: (Q-2 Revenue - Q-1 Revenue) / Q-1 Revenue")
    print(f"   3. Net Income TTM: Trailing Twelve Months Net Income")
    print(f"   4. Debt Ratio: Total Debt / Total Equity (from last year)")
    print(f"   5. Industries: {', '.join(target_industries)}")

    print(f"\n➡️  NEXT: Run Step 3:")
    print(f"    python step3_data_analysis.py")


if __name__ == "__main__":
    main()