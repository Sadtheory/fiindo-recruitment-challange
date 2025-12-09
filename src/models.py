"""
Database models for the Fiindo recruitment challenge.
This module defines SQLAlchemy ORM models for storing financial data.
"""
# src/models.py

from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime, timezone

# Create a base class for declarative class definitions
# This will be inherited by all model classes
Base = declarative_base()


class TickerStatistics(Base):
    """
    Represents financial statistics for individual stock tickers.
    Stores both raw data and calculated metrics for each company.
    """
    __tablename__ = "ticker_statistics"  # Database table name

    # Primary key - unique identifier for each record
    id = Column(Integer, primary_key=True)

    # Stock ticker symbol (e.g., AAPL, MSFT) with indexing for faster queries
    symbol = Column(String(20), nullable=False, index=True)

    # Company name
    name = Column(String(100))

    # Industry classification with indexing for grouping/filtering
    industry = Column(String(100), nullable=False, index=True)

    # ---------- CALCULATED VALUES (per challenge requirements) ----------

    # Price-to-Earnings ratio - measure of valuation
    pe_ratio = Column(Float, nullable=True)

    # Year-over-year revenue growth percentage
    revenue_growth = Column(Float, nullable=True)

    # Net Income for Trailing Twelve Months
    net_income_ttm = Column(Float, nullable=True)

    # Debt-to-Equity ratio - measure of financial leverage
    debt_ratio = Column(Float, nullable=True)

    # ---------- RAW DATA FOR TRACEABILITY ----------

    # Current stock price
    price = Column(Float, nullable=True)

    # Earnings per share or total earnings
    earnings = Column(Float, nullable=True)

    # Current fiscal year/period revenue
    revenue_current = Column(Float, nullable=True)

    # Previous fiscal year/period revenue (for growth calculation)
    revenue_previous = Column(Float, nullable=True)

    # Total company debt
    total_debt = Column(Float, nullable=True)

    # Total shareholder equity
    total_equity = Column(Float, nullable=True)

    # ---------- METADATA ----------

    # Timestamp of when this record was last updated
    # Uses UTC timezone for consistency
    last_updated = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                          onupdate=lambda: datetime.now(timezone.utc))

    # Date of the financial data (when the data was reported/effective)
    data_date = Column(DateTime, nullable=True)

    # Flag indicating if this ticker is currently active/tracked
    is_active = Column(Boolean, default=True)

    def __repr__(self):
        """String representation for debugging and logging."""
        return f"<TickerStatistics(symbol='{self.symbol}', industry='{self.industry}')>"


class IndustryAggregation(Base):
    """
    Represents aggregated financial metrics for entire industries.
    Contains summary statistics calculated from individual ticker data.
    """
    __tablename__ = "industry_aggregation"  # Database table name

    # Primary key - unique identifier for each record
    id = Column(Integer, primary_key=True)

    # Industry name - must be unique since each industry gets one aggregation record
    industry = Column(String(100), nullable=False, unique=True, index=True)

    # ---------- AGGREGATED VALUES (per challenge requirements) ----------

    # Average P/E ratio across all companies in this industry
    avg_pe_ratio = Column(Float, nullable=True)

    # Average revenue growth across all companies in this industry
    avg_revenue_growth = Column(Float, nullable=True)

    # Sum of all revenues for companies in this industry
    sum_revenue = Column(Float, nullable=True)

    # ---------- STATISTICAL DATA ----------

    # Number of tickers/companies included in this aggregation
    ticker_count = Column(Integer, default=0)

    # ---------- METADATA ----------

    # Date when this aggregation was calculated
    calculation_date = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Timestamp of when this record was last updated
    last_updated = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                          onupdate=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        """String representation for debugging and logging."""
        return f"<IndustryAggregation(industry='{self.industry}', tickers={self.ticker_count})>"