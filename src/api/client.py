# src/api/client.py

import requests
from typing import Dict, Any, Optional, List
import time
from ..utils.config import API_BASE_URL, BEARER_TOKEN, REQUEST_TIMEOUT, MAX_RETRIES
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class FiindoAPIClient:
    """Client for interacting with the Fiindo API"""

    def __init__(self):
        self.base_url = API_BASE_URL
        self.headers = {
            "Authorization": f"Bearer {BEARER_TOKEN}",
            "Content-Type": "application/json"
        }
        self.timeout = REQUEST_TIMEOUT
        self.max_retries = MAX_RETRIES

    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Optional[Dict[str, Any]]:
        """Make a request to the API with retry logic"""

        url = f"{self.base_url}{endpoint}"

        for attempt in range(self.max_retries):
            try:
                logger.info(f"Requesting {url} (Attempt {attempt + 1}/{self.max_retries})")
                response = requests.get(
                    url,
                    headers=self.headers,
                    params=params,
                    timeout=self.timeout
                )

                response.raise_for_status()
                return response.json()

            except requests.exceptions.RequestException as e:
                logger.warning(f"Request failed: {e}")
                if attempt < self.max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff
                    logger.info(f"Waiting {wait_time} seconds before retry...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"All {self.max_retries} attempts failed for {url}")
                    return None

    def get_tickers(self) -> Optional[List[Dict]]:
        """Fetch all tickers from the API"""
        # TODO: Implement based on API documentation
        # Example: return self._make_request("/api/v1/tickers")
        pass

    def get_ticker_financials(self, symbol: str) -> Optional[Dict]:
        """Fetch financial data for a specific ticker"""
        # TODO: Implement based on API documentation
        # Example: return self._make_request(f"/api/v1/tickers/{symbol}/financials")
        pass

    # Weitere Methoden nach Bedarf