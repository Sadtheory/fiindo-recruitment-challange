""" Database models for the Fiindo recruitment challenge. """
# src/models.py

from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime, timezone

Base = declarative_base()


class TickerStatistics(Base):
    __tablename__ = "ticker_statistics"

    id = Column(Integer, primary_key=True)
    symbol = Column(String(20), nullable=False, index=True)
    name = Column(String(100))
    industry = Column(String(100), nullable=False, index=True)

    # Berechnete Werte (per Challenge)
    pe_ratio = Column(Float, nullable=True)
    revenue_growth = Column(Float, nullable=True)
    net_income_ttm = Column(Float, nullable=True)
    debt_ratio = Column(Float, nullable=True)

    # Rohdaten für Nachverfolgung
    price = Column(Float, nullable=True)
    earnings = Column(Float, nullable=True)
    revenue_current = Column(Float, nullable=True)
    revenue_previous = Column(Float, nullable=True)
    total_debt = Column(Float, nullable=True)
    total_equity = Column(Float, nullable=True)

    # Metadaten
    last_updated = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                          onupdate=lambda: datetime.now(timezone.utc))
    data_date = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)

    def __repr__(self):
        return f"<TickerStatistics(symbol='{self.symbol}', industry='{self.industry}')>"


class IndustryAggregation(Base):
    __tablename__ = "industry_aggregation"

    id = Column(Integer, primary_key=True)
    industry = Column(String(100), nullable=False, unique=True, index=True)

    # Aggregierte Werte (per Challenge)
    avg_pe_ratio = Column(Float, nullable=True)
    avg_revenue_growth = Column(Float, nullable=True)
    sum_revenue = Column(Float, nullable=True)

    # Statistische Daten
    ticker_count = Column(Integer, default=0)

    # Metadaten
    calculation_date = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    last_updated = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                          onupdate=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<IndustryAggregation(industry='{self.industry}', tickers={self.ticker_count})>"