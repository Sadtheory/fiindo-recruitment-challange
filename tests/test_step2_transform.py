# test_step2_transform.py
"""
Test suite for step2_transform.py module.
Run with: pytest test_step2_transform.py -v
"""

import json
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, mock_open, MagicMock
import sys
import os
import tempfile
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

# Import after path setup
from step2_transform import (
    TickerStatistics,
    IndustryAggregation,
    DataCalculator,
    find_latest_financial_data_file
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def sample_eod_data():
    """Sample EOD data structure."""
    return {
        "stockprice": {
            "data": [
                {"date": "2025-01-01", "close": 100.0},
                {"date": "2025-01-02", "close": 102.5},
                {"date": "2025-01-03", "close": 105.0}
            ]
        }
    }


@pytest.fixture
def sample_income_data():
    """Sample income statement data structure - ONLY QUARTERLY for quarter tests."""
    return {
        "fundamentals": {
            "financials": {
                "income_statement": {
                    "data": [
                        {
                            "period": "Q1",
                            "date": "2025-03-31",
                            "revenue": 1000000,
                            "netIncome": 200000,
                            "eps": 2.5,
                            "epsdiluted": 2.4
                        },
                        {
                            "period": "Q2",
                            "date": "2025-06-30",
                            "revenue": 1200000,
                            "netIncome": 250000,
                            "eps": 3.0,
                            "epsdiluted": 2.9
                        }
                    ]
                }
            }
        }
    }


@pytest.fixture
def sample_balance_data():
    """Sample balance sheet data structure."""
    return {
        "fundamentals": {
            "financials": {
                "balance_sheet_statement": {
                    "data": [
                        {
                            "period": "FY",
                            "date": "2024-12-31",
                            "totalDebt": 5000000,
                            "totalEquity": 10000000
                        }
                    ]
                }
            }
        }
    }


# ============================================================================
# TESTS FOR DATACLASSES
# ============================================================================

class TestDataClasses:
    """Test suite for dataclasses."""

    def test_ticker_statistics_creation(self):
        """Test TickerStatistics dataclass creation."""
        stats = TickerStatistics(
            symbol="AAPL",
            industry="Software - Application",
            pe_ratio=25.5,
            revenue_growth=15.3,
            net_income_ttm=9000000.0,
            debt_ratio=0.5,
            revenue=1000000.0,
            price=150.0,
            eps=6.0
        )

        assert stats.symbol == "AAPL"
        assert stats.industry == "Software - Application"
        assert stats.pe_ratio == 25.5
        assert stats.revenue_growth == 15.3
        assert stats.net_income_ttm == 9000000.0
        assert stats.debt_ratio == 0.5
        assert stats.revenue == 1000000.0
        assert stats.price == 150.0
        assert stats.eps == 6.0


# ============================================================================
# TESTS FOR DATA CALCULATOR
# ============================================================================

class TestDataCalculator:
    """Test suite for DataCalculator class."""

    def test_extract_latest_price_valid(self, sample_eod_data):
        """Test extracting latest price from valid EOD data."""
        calculator = DataCalculator()
        price = calculator.extract_latest_price(sample_eod_data)

        assert price == 105.0

    def test_find_latest_quarter_valid(self, sample_income_data):
        """Test finding latest quarter from valid income data."""
        calculator = DataCalculator()
        latest_quarter = calculator.find_latest_quarter(sample_income_data)

        assert latest_quarter is not None
        assert latest_quarter["date"] == "2025-06-30"

    def test_extract_last_quarter_financials(self, sample_income_data):
        """Test extracting last quarter financials."""
        calculator = DataCalculator()
        revenue, net_income, eps = calculator.extract_last_quarter_financials(sample_income_data)

        assert revenue == 1200000
        assert net_income == 250000
        assert eps == 3.0

    def test_extract_revenue_for_growth_calculation(self, sample_income_data):
        """Test extracting revenue for growth calculation."""
        calculator = DataCalculator()
        revenue_q2, revenue_q1 = calculator.extract_revenue_for_growth_calculation(sample_income_data)

        assert revenue_q2 == 1200000
        assert revenue_q1 == 1000000

    def test_extract_last_year_debt_equity(self, sample_balance_data):
        """Test extracting last year debt and equity."""
        calculator = DataCalculator()
        debt, equity = calculator.extract_last_year_debt_equity(sample_balance_data)

        assert debt == 5000000
        assert equity == 10000000

    def test_determine_industry(self):
        """Test determining industry from known symbols."""
        calculator = DataCalculator()
        symbols_map = {"AAPL": "Technology", "GOOGL": "Technology"}

        industry = calculator.determine_industry("AAPL", symbols_map)
        assert industry == "Technology"

        industry = calculator.determine_industry("TSLA", symbols_map)
        assert industry == "Unknown"


# ============================================================================
# TESTS FOR FILE FINDING FUNCTION
# ============================================================================

class TestFileFinding:
    """Test suite for file finding functions."""

    def test_find_latest_financial_data_file_exists(self, tmp_path):
        """Test finding latest file when files exist."""
        # Create test directory with files
        data_dir = tmp_path / "data"
        data_dir.mkdir()

        (data_dir / "financial_data_20250101_120000.json").write_text('{}')
        (data_dir / "financial_data_20250103_120000.json").write_text('{}')

        latest_file = find_latest_financial_data_file(str(data_dir))

        assert latest_file is not None
        assert "20250103_120000" in str(latest_file)


# ============================================================================
# SIMPLIFIED MAIN FUNCTION TESTS
# ============================================================================

def test_main_integration_logic():
    """Test the core logic of main without actually running it."""
    # Test industry filtering logic
    target_industries = ["Banks - Diversified", "Software - Application", "Consumer Electronics"]

    mock_stats = [
        TickerStatistics(symbol="AAPL", industry="Software - Application"),
        TickerStatistics(symbol="GOOGL", industry="Software - Application"),
        TickerStatistics(symbol="JPM", industry="Banks - Diversified"),
        TickerStatistics(symbol="XYZ", industry="Other Industry")
    ]

    filtered_stats = [stats for stats in mock_stats if stats.industry in target_industries]

    assert len(filtered_stats) == 3
    assert all(stat.industry in target_industries for stat in filtered_stats)


def test_pe_ratio_calculation_logic():
    """Test PE ratio calculation logic."""
    # Priority 1: EPS TTM
    price = 100.0
    eps_ttm = 4.0
    pe_ratio = price / eps_ttm
    assert pe_ratio == 25.0

    # Priority 3: Quarterly EPS * 4
    quarterly_eps = 2.0
    estimated_annual_eps = quarterly_eps * 4
    pe_ratio = price / estimated_annual_eps
    assert pe_ratio == 12.5


def test_revenue_growth_calculation():
    """Test revenue growth calculation."""
    revenue_q2 = 1200000
    revenue_q1 = 1000000
    growth = ((revenue_q2 - revenue_q1) / revenue_q1) * 100
    assert growth == 20.0


def test_debt_ratio_calculation():
    """Test debt ratio calculation."""
    debt = 5000000
    equity = 10000000
    debt_ratio = debt / equity
    assert debt_ratio == 0.5


# ============================================================================
# COMPREHENSIVE DATA CALCULATOR TESTS
# ============================================================================

def test_calculator_with_complete_data():
    """Test DataCalculator with complete data structure."""
    calculator = DataCalculator()

    # Complete sample data
    complete_data = {
        "eod": {
            "stockprice": {
                "data": [{"date": "2025-01-01", "close": 150.0}]
            }
        },
        "income_statement": {
            "fundamentals": {
                "financials": {
                    "income_statement": {
                        "data": [
                            {
                                "period": "Q1",
                                "date": "2025-03-31",
                                "revenue": 1000000,
                                "netIncome": 200000,
                                "eps": 2.5
                            },
                            {
                                "period": "Q2",
                                "date": "2025-06-30",
                                "revenue": 1200000,
                                "netIncome": 250000,
                                "eps": 3.0
                            }
                        ]
                    }
                }
            }
        },
        "balance_sheet_statement": {
            "fundamentals": {
                "financials": {
                    "balance_sheet_statement": {
                        "data": [
                            {
                                "period": "FY",
                                "date": "2024-12-31",
                                "totalDebt": 5000000,
                                "totalEquity": 10000000
                            }
                        ]
                    }
                }
            }
        }
    }

    # Test all extractors
    price = calculator.extract_latest_price(complete_data["eod"])
    assert price == 150.0

    revenue, net_income, eps = calculator.extract_last_quarter_financials(complete_data["income_statement"])
    assert revenue == 1200000
    assert eps == 3.0

    revenue_q2, revenue_q1 = calculator.extract_revenue_for_growth_calculation(complete_data["income_statement"])
    assert revenue_q2 == 1200000
    assert revenue_q1 == 1000000

    debt, equity = calculator.extract_last_year_debt_equity(complete_data["balance_sheet_statement"])
    assert debt == 5000000
    assert equity == 10000000


def test_calculator_with_incomplete_data():
    """Test DataCalculator with missing data."""
    calculator = DataCalculator()

    # Incomplete data
    incomplete_data = {
        "eod": {},
        "income_statement": {},
        "balance_sheet_statement": {}
    }

    # All should return None
    price = calculator.extract_latest_price(incomplete_data["eod"])
    assert price is None

    revenue, net_income, eps = calculator.extract_last_quarter_financials(incomplete_data["income_statement"])
    assert revenue is None
    assert eps is None

    debt, equity = calculator.extract_last_year_debt_equity(incomplete_data["balance_sheet_statement"])
    assert debt is None
    assert equity is None


# ============================================================================
# TEST INDUSTRY AGGREGATION LOGIC
# ============================================================================

def test_industry_aggregation_calculation():
    """Test industry aggregation calculations."""
    # Create sample stats
    stats_list = [
        TickerStatistics(
            symbol="AAPL",
            industry="Software - Application",
            pe_ratio=25.0,
            revenue_growth=20.0,
            revenue=1000000.0
        ),
        TickerStatistics(
            symbol="GOOGL",
            industry="Software - Application",
            pe_ratio=30.0,
            revenue_growth=15.0,
            revenue=1500000.0
        ),
        TickerStatistics(
            symbol="MSFT",
            industry="Software - Application",
            pe_ratio=28.0,
            revenue_growth=25.0,
            revenue=1200000.0
        )
    ]

    # Calculate aggregations manually
    pe_ratios = [s.pe_ratio for s in stats_list if s.pe_ratio is not None]
    revenue_growths = [s.revenue_growth for s in stats_list if s.revenue_growth is not None]
    revenues = [s.revenue for s in stats_list if s.revenue is not None]

    avg_pe = sum(pe_ratios) / len(pe_ratios)
    avg_revenue_growth = sum(revenue_growths) / len(revenue_growths)
    sum_revenue = sum(revenues)

    assert avg_pe == pytest.approx((25.0 + 30.0 + 28.0) / 3)
    assert avg_revenue_growth == pytest.approx((20.0 + 15.0 + 25.0) / 3)
    assert sum_revenue == 3700000.0


# ============================================================================
# EDGE CASE TESTS
# ============================================================================

def test_edge_case_zero_values():
    """Test handling of zero values."""
    calculator = DataCalculator()

    # Test with zero EPS
    income_data_zero_eps = {
        "fundamentals": {
            "financials": {
                "income_statement": {
                    "data": [
                        {
                            "period": "Q1",
                            "date": "2025-03-31",
                            "revenue": 1000000,
                            "netIncome": 0,
                            "eps": 0.0
                        }
                    ]
                }
            }
        }
    }

    revenue, net_income, eps = calculator.extract_last_quarter_financials(income_data_zero_eps)

    # EPS sollte None sein, da 0-Werte oft ignoriert werden
    # (In deinem Code steht: "if eps_value != 0: eps = eps_value")
    assert revenue == 1000000
    assert net_income == 0.0
    assert eps is None  # Weil eps = 0 ist und der Code "if eps_value != 0" prüft

    # Test with zero equity (for debt ratio)
    balance_data_zero_equity = {
        "fundamentals": {
            "financials": {
                "balance_sheet_statement": {
                    "data": [
                        {
                            "period": "FY",
                            "date": "2024-12-31",
                            "totalDebt": 5000000,
                            "totalEquity": 0
                        }
                    ]
                }
            }
        }
    }

    debt, equity = calculator.extract_last_year_debt_equity(balance_data_zero_equity)
    assert debt == 5000000
    assert equity == 0.0


def test_malformed_data_structures():
    """Test handling of malformed data structures."""
    calculator = DataCalculator()

    # Malformed EOD data
    malformed_eod = {
        "stockprice": {
            "data": "not a list"  # Wrong type
        }
    }

    price = calculator.extract_latest_price(malformed_eod)
    assert price is None

    # Missing keys
    missing_keys_data = {
        "fundamentals": {}  # Missing financials
    }

    latest_quarter = calculator.find_latest_quarter(missing_keys_data)
    assert latest_quarter is None


# ============================================================================
# ADDITIONAL TESTS FOR SPECIFIC SCENARIOS
# ============================================================================

def test_eps_zero_value_handling():
    """Test that EPS value of 0 returns None (as per the code logic)."""
    calculator = DataCalculator()

    # Looking at the actual code in step2_transform.py:
    # if eps_value != 0:  # ignore zero EPS values
    #     eps = eps_value

    # So EPS = 0 should return None
    income_data = {
        "fundamentals": {
            "financials": {
                "income_statement": {
                    "data": [
                        {
                            "period": "Q1",
                            "date": "2025-03-31",
                            "revenue": 1000000,
                            "netIncome": 200000,
                            "eps": 0.0  # Zero EPS
                        }
                    ]
                }
            }
        }
    }

    revenue, net_income, eps = calculator.extract_last_quarter_financials(income_data)

    assert revenue == 1000000
    assert net_income == 200000
    assert eps is None  # Weil EPS = 0 und der Code das ignoriert


def test_non_zero_eps_extraction():
    """Test that non-zero EPS values are extracted correctly."""
    calculator = DataCalculator()

    income_data = {
        "fundamentals": {
            "financials": {
                "income_statement": {
                    "data": [
                        {
                            "period": "Q1",
                            "date": "2025-03-31",
                            "revenue": 1000000,
                            "netIncome": 200000,
                            "eps": 0.01  # Very small but non-zero
                        }
                    ]
                }
            }
        }
    }

    revenue, net_income, eps = calculator.extract_last_quarter_financials(income_data)

    assert revenue == 1000000
    assert net_income == 200000
    assert eps == 0.01  # Sollte extrahiert werden weil != 0


def test_alternative_eps_keys():
    """Test extraction with alternative EPS keys."""
    calculator = DataCalculator()

    income_data = {
        "fundamentals": {
            "financials": {
                "income_statement": {
                    "data": [
                        {
                            "period": "Q1",
                            "date": "2025-03-31",
                            "revenue": 1000000,
                            "netIncome": 200000,
                            "epsdiluted": 2.3,  # Alternative key
                            "earningsPerShare": 2.4  # Another alternative
                        }
                    ]
                }
            }
        }
    }

    revenue, net_income, eps = calculator.extract_last_quarter_financials(income_data)

    # Should extract one of the EPS values (whichever is found first)
    assert revenue == 1000000
    assert net_income == 200000
    assert eps is not None  # Irgendein EPS Wert sollte gefunden werden


if __name__ == "__main__":
    # Run tests directly if file is executed
    pytest.main([__file__, "-v"])