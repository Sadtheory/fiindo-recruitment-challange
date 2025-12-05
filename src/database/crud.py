# src/database/crud.py

from sqlalchemy.orm import Session
from typing import List, Optional
from ..models import TickerStatistics, IndustryAggregation
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class CRUDOperations:
    """Database CRUD operations for the challenge"""

    @staticmethod
    def create_or_update_ticker_statistics(db: Session, ticker_data: dict) -> TickerStatistics:
        """Create or update ticker statistics in database"""

        # Prüfen, ob der Ticker bereits existiert
        ticker = db.query(TickerStatistics).filter(
            TickerStatistics.symbol == ticker_data['symbol']
        ).first()

        if ticker:
            # Update existing ticker
            for key, value in ticker_data.items():
                setattr(ticker, key, value)
            logger.info(f"Updated ticker: {ticker_data['symbol']}")
        else:
            # Create new ticker
            ticker = TickerStatistics(**ticker_data)
            db.add(ticker)
            logger.info(f"Created new ticker: {ticker_data['symbol']}")

        db.commit()
        db.refresh(ticker)
        return ticker

    @staticmethod
    def create_or_update_industry_aggregation(db: Session, industry_data: dict) -> IndustryAggregation:
        """Create or update industry aggregation in database"""

        industry = db.query(IndustryAggregation).filter(
            IndustryAggregation.industry == industry_data['industry']
        ).first()

        if industry:
            for key, value in industry_data.items():
                setattr(industry, key, value)
            logger.info(f"Updated industry aggregation: {industry_data['industry']}")
        else:
            industry = IndustryAggregation(**industry_data)
            db.add(industry)
            logger.info(f"Created new industry aggregation: {industry_data['industry']}")

        db.commit()
        db.refresh(industry)
        return industry

    @staticmethod
    def get_all_ticker_statistics(db: Session) -> List[TickerStatistics]:
        """Retrieve all ticker statistics from database"""
        return db.query(TickerStatistics).all()

    @staticmethod
    def get_ticker_statistics_by_industry(db: Session, industry: str) -> List[TickerStatistics]:
        """Retrieve ticker statistics for a specific industry"""
        return db.query(TickerStatistics).filter(
            TickerStatistics.industry == industry
        ).all()

    @staticmethod
    def get_all_industry_aggregations(db: Session) -> List[IndustryAggregation]:
        """Retrieve all industry aggregations from database"""
        return db.query(IndustryAggregation).all()