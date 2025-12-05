# src/calculations/financial_calculations.py

from typing import Dict, Any, Optional
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class FinancialCalculations:
    """Class for financial calculations required by the challenge"""

    @staticmethod
    def calculate_pe_ratio(price: float, earnings: float) -> Optional[float]:
        """Calculate Price-to-Earnings ratio"""
        if earnings and earnings != 0:
            return price / earnings
        return None

    @staticmethod
    def calculate_revenue_growth(current_revenue: float, previous_revenue: float) -> Optional[float]:
        """Calculate quarter-over-quarter revenue growth"""
        if previous_revenue and previous_revenue != 0:
            return ((current_revenue - previous_revenue) / previous_revenue) * 100
        return None

    @staticmethod
    def calculate_debt_ratio(total_debt: float, total_equity: float) -> Optional[float]:
        """Calculate debt-to-equity ratio"""
        if total_equity and total_equity != 0:
            return total_debt / total_equity
        return None

    @staticmethod
    def calculate_industry_aggregations(ticker_data_list: list) -> Dict[str, Any]:
        """Calculate industry-wide aggregations"""
        # Gruppiere nach Industrie
        industry_data = {}

        for ticker in ticker_data_list:
            industry = ticker.get('industry')
            if industry not in industry_data:
                industry_data[industry] = {
                    'pe_ratios': [],
                    'revenue_growths': [],
                    'revenues': []
                }

            if ticker.get('pe_ratio') is not None:
                industry_data[industry]['pe_ratios'].append(ticker['pe_ratio'])

            if ticker.get('revenue_growth') is not None:
                industry_data[industry]['revenue_growths'].append(ticker['revenue_growth'])

            if ticker.get('revenue_current') is not None:
                industry_data[industry]['revenues'].append(ticker['revenue_current'])

        # Aggregationen berechnen
        aggregations = {}
        for industry, data in industry_data.items():
            avg_pe = sum(data['pe_ratios']) / len(data['pe_ratios']) if data['pe_ratios'] else None
            avg_revenue_growth = sum(data['revenue_growths']) / len(data['revenue_growths']) if data[
                'revenue_growths'] else None
            sum_revenue = sum(data['revenues']) if data['revenues'] else None

            aggregations[industry] = {
                'avg_pe_ratio': avg_pe,
                'avg_revenue_growth': avg_revenue_growth,
                'sum_revenue': sum_revenue,
                'ticker_count': len(data['revenues'])
            }

        return aggregations