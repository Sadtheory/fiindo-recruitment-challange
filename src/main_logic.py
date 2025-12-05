# src/main_logic.py

from .database.session import SessionLocal
from .api.client import FiindoAPIClient
from .calculations.financial_calculations import FinancialCalculations
from .database.crud import CRUDOperations
from .utils.config import TARGET_INDUSTRIES
from .utils.logger import setup_logger
from typing import List, Dict

logger = setup_logger(__name__)


class FiindoChallenge:
    """Main class orchestrating the entire ETL process"""

    def __init__(self):
        self.api_client = FiindoAPIClient()
        self.calculations = FinancialCalculations()
        self.db = SessionLocal()

    def run(self):
        """Main execution method"""
        logger.info("Starting Fiindo Challenge ETL process")

        try:
            # 1. Daten von API abrufen
            tickers_data = self.fetch_ticker_data()

            # 2. Berechnungen durchführen
            calculated_data = self.calculate_statistics(tickers_data)

            # 3. In Datenbank speichern
            self.save_to_database(calculated_data)

            logger.info("ETL process completed successfully")

        except Exception as e:
            logger.error(f"ETL process failed: {e}", exc_info=True)
            raise
        finally:
            self.db.close()

    def fetch_ticker_data(self) -> List[Dict]:
        """Fetch ticker data from API"""
        logger.info("Fetching ticker data from API...")
        # TODO: Implement actual API call
        # Example:
        # all_tickers = self.api_client.get_tickers()
        # Filter for target industries
        # return filtered_tickers

        # Temporäre Dummy-Daten für Test
        return []

    def calculate_statistics(self, tickers_data: List[Dict]) -> Dict:
        """Calculate financial statistics for tickers"""
        logger.info("Calculating financial statistics...")

        calculated_tickers = []

        for ticker in tickers_data:
            # TODO: Replace with actual calculations from API data
            calculated = {
                'symbol': ticker.get('symbol'),
                'name': ticker.get('name'),
                'industry': ticker.get('industry'),
                'pe_ratio': self.calculations.calculate_pe_ratio(
                    ticker.get('price'),
                    ticker.get('earnings')
                ),
                'revenue_growth': self.calculations.calculate_revenue_growth(
                    ticker.get('revenue_current'),
                    ticker.get('revenue_previous')
                ),
                'net_income_ttm': ticker.get('net_income_ttm'),
                'debt_ratio': self.calculations.calculate_debt_ratio(
                    ticker.get('total_debt'),
                    ticker.get('total_equity')
                )
            }
            calculated_tickers.append(calculated)

        # Industry aggregations
        industry_aggregations = self.calculations.calculate_industry_aggregations(calculated_tickers)

        return {
            'ticker_statistics': calculated_tickers,
            'industry_aggregations': industry_aggregations
        }

    def save_to_database(self, data: Dict):
        """Save calculated data to database"""
        logger.info("Saving data to database...")

        # Save ticker statistics
        for ticker_data in data['ticker_statistics']:
            CRUDOperations.create_or_update_ticker_statistics(self.db, ticker_data)

        # Save industry aggregations
        for industry_name, agg_data in data['industry_aggregations'].items():
            industry_data = {
                'industry': industry_name,
                'avg_pe_ratio': agg_data.get('avg_pe_ratio'),
                'avg_revenue_growth': agg_data.get('avg_revenue_growth'),
                'sum_revenue': agg_data.get('sum_revenue'),
                'ticker_count': agg_data.get('ticker_count', 0)
            }
            CRUDOperations.create_or_update_industry_aggregation(self.db, industry_data)

        logger.info(
            f"Saved {len(data['ticker_statistics'])} tickers and {len(data['industry_aggregations'])} industries")