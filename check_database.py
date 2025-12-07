# check_database.py

import sqlite3
from tabulate import tabulate


def check_database():
    """Überprüft den Datenbankinhalt"""

    print("🔍 Checking database content...")

    try:
        conn = sqlite3.connect('data/fiindo_challenge.db')
        cursor = conn.cursor()

        # 1. Tabellen auflisten
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print("\n📋 Tables in database:")
        for table in tables:
            print(f"  • {table[0]}")

        # 2. Ticker Statistics anzeigen
        print("\n📊 TICKER STATISTICS:")
        cursor.execute("""
                       SELECT symbol,
                              industry,
                              pe_ratio,
                              revenue_growth,
                              net_income_ttm,
                              debt_ratio,
                              price,
                              revenue_current
                       FROM ticker_statistics
                       ORDER BY industry, symbol
                       """)

        columns = [description[0] for description in cursor.description]
        rows = cursor.fetchall()

        if rows:
            print(tabulate(rows, headers=columns, floatfmt=".2f", tablefmt="grid"))
        else:
            print("  No data found")

        # 3. Industry Aggregation anzeigen
        print("\n🏢 INDUSTRY AGGREGATION:")
        cursor.execute("""
                       SELECT industry,
                              ticker_count,
                              avg_pe_ratio,
                              avg_revenue_growth,
                              sum_revenue
                       FROM industry_aggregation
                       ORDER BY industry
                       """)

        columns = [description[0] for description in cursor.description]
        rows = cursor.fetchall()

        if rows:
            print(tabulate(rows, headers=columns, floatfmt=".2f", tablefmt="grid"))
        else:
            print("  No data found")

        # 4. Statistische Zusammenfassung
        print("\n📈 STATISTICAL SUMMARY:")

        # PE Ratios
        cursor.execute("""
                       SELECT industry,
                              COUNT(pe_ratio) as count_with_pe,
                              AVG(pe_ratio)   as avg_pe,
                              MIN(pe_ratio)   as min_pe,
                              MAX(pe_ratio)   as max_pe
                       FROM ticker_statistics
                       WHERE pe_ratio IS NOT NULL
                       GROUP BY industry
                       """)

        print("PE Ratios by Industry:")
        pe_data = cursor.fetchall()
        if pe_data:
            print(tabulate(pe_data,
                           headers=["Industry", "Count", "Avg", "Min", "Max"],
                           floatfmt=".2f",
                           tablefmt="grid"))

        # Revenue Growth
        cursor.execute("""
                       SELECT industry,
                              COUNT(revenue_growth) as count_with_growth,
                              AVG(revenue_growth)   as avg_growth,
                              MIN(revenue_growth)   as min_growth,
                              MAX(revenue_growth)   as max_growth
                       FROM ticker_statistics
                       WHERE revenue_growth IS NOT NULL
                       GROUP BY industry
                       """)

        print("\nRevenue Growth by Industry (%):")
        growth_data = cursor.fetchall()
        if growth_data:
            print(tabulate(growth_data,
                           headers=["Industry", "Count", "Avg", "Min", "Max"],
                           floatfmt=".2f",
                           tablefmt="grid"))

        conn.close()
        print("\n✅ Database check completed")

    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")


if __name__ == "__main__":
    check_database()