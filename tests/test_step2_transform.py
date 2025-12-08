# tests/test_step2.py
import pytest
import sys
import os

# WICHTIG: Füge src Verzeichnis zum Python-Pfad hinzu
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
src_dir = os.path.join(parent_dir, 'src')
sys.path.insert(0, src_dir)

# Jetzt können wir step2_calculations aus src importieren
from step2_calculations import (
    TickerStatistics,
    IndustryAggregation,
    DataCalculator,
    main,
    find_latest_financial_data_file  # Falls vorhanden
)


def test_step2_import():
    """Test dass step2_calculations korrekt importiert werden kann"""
    # Prüfe DataClasses
    assert TickerStatistics is not None
    assert IndustryAggregation is not None

    # Prüfe Calculator Klasse
    assert DataCalculator is not None

    # Prüfe Hauptfunktion
    assert main is not None
    assert callable(main)

    print("✅ Step 2 import successful")


def test_dataclasses():
    """Test der DataClasses Struktur"""
    # Test TickerStatistics
    stats = TickerStatistics(
        symbol="AAPL.US",
        industry="Consumer Electronics",
        pe_ratio=25.5,
        revenue_growth=10.2,
        net_income_ttm=100_000_000,
        debt_ratio=1.5,
        revenue=400_000_000_000
    )

    assert stats.symbol == "AAPL.US"
    assert stats.industry == "Consumer Electronics"
    assert stats.pe_ratio == 25.5
    assert stats.revenue_growth == 10.2
    assert stats.debt_ratio == 1.5

    print("✅ TickerStatistics dataclass works")


def test_industry_aggregation():
    """Test der IndustryAggregation DataClass"""
    agg = IndustryAggregation(
        industry="Software - Application",
        avg_pe_ratio=30.2,
        avg_revenue_growth=15.5,
        sum_revenue=50_000_000_000,
        ticker_count=5
    )

    assert agg.industry == "Software - Application"
    assert agg.avg_pe_ratio == 30.2
    assert agg.avg_revenue_growth == 15.5
    assert agg.ticker_count == 5

    print("✅ IndustryAggregation dataclass works")


def test_datacalculator_methods():
    """Test der DataCalculator Methoden"""
    calculator = DataCalculator()

    # Prüfe alle wichtigen Methoden
    methods = [
        'extract_latest_price',
        'find_latest_quarter',
        'extract_last_quarter_financials',
        'extract_revenue_for_growth_calculation',
        'extract_last_year_debt_equity',
        'extract_net_income_ttm',
        'determine_industry'
    ]

    for method in methods:
        assert hasattr(calculator, method), f"Missing method: {method}"
        assert callable(getattr(calculator, method)), f"Method not callable: {method}"

    print("✅ DataCalculator has all required methods")


def test_industry_detection():
    """Test der Industrie-Erkennung"""
    calculator = DataCalculator()

    # Test verschiedene Symbole
    test_cases = [
        ("JPM.US", "Banks - Diversified"),
        ("BAC.US", "Banks - Diversified"),
        ("AAPL.US", "Consumer Electronics"),
        ("NVDA.US", "Consumer Electronics"),
        ("MSFT.US", "Software - Application"),
        ("ORCL.US", "Software - Application"),
        ("UNKNOWN.US", "Unknown")
    ]

    for symbol, expected_industry in test_cases:
        result = calculator.determine_industry(symbol)
        assert result == expected_industry, f"Failed for {symbol}: got {result}, expected {expected_industry}"

    print("✅ Industry detection works correctly")


if __name__ == "__main__":
    # Führe alle Tests aus
    test_step2_import()
    test_dataclasses()
    test_industry_aggregation()
    test_datacalculator_methods()
    test_industry_detection()

    print("\n🎉 All Step 2 tests completed!")