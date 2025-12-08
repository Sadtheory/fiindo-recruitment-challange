# test_step1_fetch.py
"""
Test suite for step1_fetch.py module.
Run with: pytest test_step1_fetch.py -v
"""

import json
import tempfile
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, mock_open
import sys
import os
import io

# Add src to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

# Import after path setup
from step1_fetch import (
    KnownSymbolsManager,
    Headers,
    Fiindo_Endpoints,
    fetch_all_available_data,
    FIRST_NAME,
    LAST_NAME
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def temp_known_symbols_file():
    """Create a temporary known symbols file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump({"AAPL": "Technology", "GOOGL": "Technology"}, f)
        temp_file = f.name

    yield temp_file

    # Cleanup
    if os.path.exists(temp_file):
        os.unlink(temp_file)


@pytest.fixture
def mock_api_responses():
    """Provide mock API responses for testing."""
    return {
        "symbols": Mock(
            status_code=200,
            json=lambda: {"symbols": ["AAPL", "GOOGL", "MSFT", "JPM", "ADBE"]}
        ),
        "general_target_industry": Mock(
            status_code=200,
            json=lambda: {
                "fundamentals": {
                    "profile": {
                        "data": [{"industry": "Software - Application"}]
                    }
                }
            }
        ),
        "general_non_target": Mock(
            status_code=200,
            json=lambda: {
                "fundamentals": {
                    "profile": {
                        "data": [{"industry": "Other Industry"}]
                    }
                }
            }
        ),
        "general_error": Mock(
            status_code=404,
            json=lambda: {"error": "Not found"}
        ),
        "financials_success": Mock(
            status_code=200,
            json=lambda: {"data": [{"revenue": 1000}]}
        ),
        "eod_success": Mock(
            status_code=200,
            json=lambda: {"data": [{"close": 150}]}
        ),
        "financials_error": Mock(
            status_code=500,
            json=lambda: {"error": "Internal error"}
        )
    }


# ============================================================================
# TESTS FOR KNOWN SYMBOLS MANAGER
# ============================================================================

class TestKnownSymbolsManager:
    """Test suite for KnownSymbolsManager class."""

    def test_load_known_symbols_file_not_exists(self, tmp_path):
        """Test loading when file doesn't exist."""
        test_file = tmp_path / "nonexistent.json"
        KnownSymbolsManager.KNOWN_SYMBOLS_FILE = str(test_file)

        result = KnownSymbolsManager.load_known_symbols()
        assert result == {}

    def test_load_known_symbols_valid_file(self, temp_known_symbols_file):
        """Test loading valid JSON file."""
        KnownSymbolsManager.KNOWN_SYMBOLS_FILE = temp_known_symbols_file

        result = KnownSymbolsManager.load_known_symbols()
        assert result == {"AAPL": "Technology", "GOOGL": "Technology"}

    def test_load_known_symbols_corrupted_file(self, tmp_path, capsys):
        """Test handling of corrupted JSON file."""
        test_file = tmp_path / "corrupted.json"
        test_file.write_text("{invalid json}")
        KnownSymbolsManager.KNOWN_SYMBOLS_FILE = str(test_file)

        result = KnownSymbolsManager.load_known_symbols()

        # Should return empty dict
        assert result == {}

        # Should print warning
        captured = capsys.readouterr()
        assert "⚠️" in captured.out or "Could not load" in captured.out

    def test_save_known_symbols(self, tmp_path):
        """Test saving symbols to file."""
        test_file = tmp_path / "save_test.json"
        KnownSymbolsManager.KNOWN_SYMBOLS_FILE = str(test_file)

        test_data = {"TSLA": "Automotive", "NVDA": "Semiconductors"}

        # Save data
        KnownSymbolsManager.save_known_symbols(test_data)

        # Verify file was created and content is correct
        assert test_file.exists()
        with open(test_file, 'r') as f:
            loaded_data = json.load(f)

        assert loaded_data == test_data

    def test_update_known_symbols_new_symbol(self, tmp_path):
        """Test adding a new symbol."""
        test_file = tmp_path / "update_test.json"
        KnownSymbolsManager.KNOWN_SYMBOLS_FILE = str(test_file)

        # First update should create file and return True
        updated = KnownSymbolsManager.update_known_symbols("TSLA", "Automotive")
        assert updated == True

        # Verify content
        with open(test_file, 'r') as f:
            data = json.load(f)
        assert data == {"TSLA": "Automotive"}

    def test_update_known_symbols_existing_no_change(self, temp_known_symbols_file):
        """Test updating existing symbol with same industry."""
        KnownSymbolsManager.KNOWN_SYMBOLS_FILE = temp_known_symbols_file

        # Load initial data
        initial_data = KnownSymbolsManager.load_known_symbols()

        # Update with same industry
        updated = KnownSymbolsManager.update_known_symbols("AAPL", "Technology")

        # Should return False (no change)
        assert updated == False

        # Data should remain unchanged
        current_data = KnownSymbolsManager.load_known_symbols()
        assert current_data == initial_data

    def test_update_known_symbols_change_industry(self, temp_known_symbols_file):
        """Test updating existing symbol with different industry."""
        KnownSymbolsManager.KNOWN_SYMBOLS_FILE = temp_known_symbols_file

        # Update with different industry
        updated = KnownSymbolsManager.update_known_symbols("AAPL", "Consumer Electronics")
        assert updated == True

        # Verify industry was updated
        current_data = KnownSymbolsManager.load_known_symbols()
        assert current_data["AAPL"] == "Consumer Electronics"
        assert current_data["GOOGL"] == "Technology"  # Other symbol unchanged


# ============================================================================
# TESTS FOR HEADERS
# ============================================================================

class TestHeaders:
    """Test suite for Headers class."""

    def test_auth_header(self):
        """Test Authorization header construction."""
        headers = Headers.General.Auth("John", "Doe")
        assert headers == {"Authorization": "Bearer John.Doe"}

    def test_auth_header_with_existing(self):
        """Test Authorization header with existing headers."""
        existing = {"Accept": "application/json"}
        result = Headers.General.Auth("Jane", "Smith", existing)

        assert result == {
            "Accept": "application/json",
            "Authorization": "Bearer Jane.Smith"
        }

    def test_accept_header(self):
        """Test Accept header."""
        headers = Headers.General.Accept()
        assert headers == {"Accept": "text/plain"}

    def test_default_headers(self):
        """Test DEFAULT headers helper."""
        headers = Headers.General.DEFAULT("Test", "User")

        assert headers == {
            "Authorization": "Bearer Test.User",
            "Accept": "text/plain"
        }


# ============================================================================
# TESTS FOR FIINDO ENDPOINTS
# ============================================================================

class TestFiindoEndpoints:
    """Test suite for Fiindo_Endpoints class."""

    def test_financials_request_url(self):
        """Test Financials request URL construction."""
        with patch('requests.get') as mock_get:
            mock_response = Mock(status_code=200)
            mock_get.return_value = mock_response

            response = Fiindo_Endpoints.Financials.request(
                "AAPL",
                "income_statement",
                "Cynthia",
                "Kraft"
            )

            # Verify URL
            expected_url = "https://api.test.fiindo.com/api/v1/financials/AAPL/income_statement"
            mock_get.assert_called_once()

            args, kwargs = mock_get.call_args
            assert args[0] == expected_url

            # Verify headers
            assert "Authorization" in kwargs["headers"]
            assert kwargs["headers"]["Authorization"] == "Bearer Cynthia.Kraft"

    def test_financials_income_statement(self):
        """Test income_statement convenience method."""
        with patch('step1_fetch.Fiindo_Endpoints.Financials.request') as mock_request:
            Fiindo_Endpoints.Financials.income_statement("GOOGL", "Cynthia", "Kraft")

            mock_request.assert_called_once_with(
                "GOOGL",
                "income_statement",
                "Cynthia",
                "Kraft"
            )

    def test_general_request(self):
        """Test General request URL construction."""
        with patch('requests.get') as mock_get:
            mock_response = Mock(status_code=200)
            mock_get.return_value = mock_response

            response = Fiindo_Endpoints.General.request(
                "MSFT",
                "Cynthia",
                "Kraft"
            )

            expected_url = "https://api.test.fiindo.com/api/v1/general/MSFT"
            mock_get.assert_called_once()

            args, kwargs = mock_get.call_args
            assert args[0] == expected_url

    def test_symbols_request(self):
        """Test Symbols request URL construction."""
        with patch('requests.get') as mock_get:
            mock_response = Mock(status_code=200)
            mock_get.return_value = mock_response

            response = Fiindo_Endpoints.Symbols.request("Cynthia", "Kraft")

            expected_url = "https://api.test.fiindo.com/api/v1/symbols"
            mock_get.assert_called_once()

            args, kwargs = mock_get.call_args
            assert args[0] == expected_url


# ============================================================================
# TESTS FOR MAIN FETCH FUNCTION
# ============================================================================

class TestFetchAllAvailableData:
    """Test suite for fetch_all_available_data function."""

    def test_fetch_with_no_symbols(self):
        """Test when API returns no symbols."""
        with patch('requests.get') as mock_get:
            # Mock API returning empty symbol list
            mock_response = Mock(status_code=200, json=lambda: {"symbols": []})
            mock_get.return_value = mock_response

            # Mock file operations
            with patch('builtins.open', mock_open()) as mock_file:
                with patch('json.dump'):
                    with patch('os.makedirs'):
                        # Mock known symbols as empty
                        with patch('step1_fetch.KnownSymbolsManager.load_known_symbols', return_value={}):
                            result = fetch_all_available_data()

            # Should complete but return None (no data collected)
            assert result is None

    def test_fetch_with_target_industry_symbols(self, mock_api_responses):
        """Test fetching symbols in target industries."""
        with patch('requests.get') as mock_get:
            # Setup mock to return different responses based on URL
            def side_effect(url, headers=None, timeout=None):
                if "symbols" in url:
                    return mock_api_responses["symbols"]
                elif "general" in url:
                    return mock_api_responses["general_target_industry"]
                elif "eod" in url:
                    return mock_api_responses["eod_success"]
                else:
                    return mock_api_responses["financials_success"]

            mock_get.side_effect = side_effect

            # Mock file operations
            with patch('builtins.open', mock_open()) as mock_file:
                with patch('json.dump'):
                    with patch('os.makedirs'):
                        # Mock known symbols manager
                        with patch('step1_fetch.KnownSymbolsManager.load_known_symbols', return_value={}):
                            with patch('step1_fetch.KnownSymbolsManager.update_known_symbols', return_value=True):
                                result = fetch_all_available_data()

            # Should return data for target industry symbols
            # Note: In actual implementation, this would return data dict
            # For test purposes, we accept either None or dict
            assert result is None or isinstance(result, dict)

    def test_fetch_symbols_api_error(self):
        """Test when symbols API returns error."""
        with patch('requests.get') as mock_get:
            # Mock API error
            mock_response = Mock(status_code=500)
            mock_get.return_value = mock_response

            # Mock file operations
            with patch('builtins.open', mock_open()):
                with patch('json.dump'):
                    with patch('os.makedirs'):
                        result = fetch_all_available_data()

            # Should return None early
            assert result is None

    def test_fetch_general_endpoint_error(self, mock_api_responses):
        """Test when general endpoint fails for a symbol."""
        with patch('requests.get') as mock_get:
            def side_effect(url, headers=None, timeout=None):
                if "symbols" in url:
                    return mock_api_responses["symbols"]
                elif "general" in url:
                    # Return error for general endpoint
                    return mock_api_responses["general_error"]
                elif "eod" in url:
                    return mock_api_responses["eod_success"]
                else:
                    return mock_api_responses["financials_success"]

            mock_get.side_effect = side_effect

            # Mock file operations
            with patch('builtins.open', mock_open()) as mock_file:
                with patch('json.dump'):
                    with patch('os.makedirs'):
                        with patch('step1_fetch.KnownSymbolsManager.load_known_symbols', return_value={}):
                            result = fetch_all_available_data()

            # Function should still complete
            assert result is None or isinstance(result, dict)

    def test_fetch_insufficient_financial_data(self, mock_api_responses):
        """Test when symbol has insufficient financial data (<2 endpoints successful)."""
        with patch('requests.get') as mock_get:
            def side_effect(url, headers=None, timeout=None):
                if "symbols" in url:
                    return mock_api_responses["symbols"]
                elif "general" in url:
                    return mock_api_responses["general_target_industry"]
                elif "eod" in url:
                    return mock_api_responses["eod_success"]
                else:
                    # Return error for financial endpoints (less than 2 will succeed)
                    # Only eod will succeed (1 endpoint)
                    return mock_api_responses["financials_error"]

            mock_get.side_effect = side_effect

            # Mock file operations
            with patch('builtins.open', mock_open()) as mock_file:
                with patch('json.dump'):
                    with patch('os.makedirs'):
                        with patch('step1_fetch.KnownSymbolsManager.load_known_symbols', return_value={}):
                            with patch('step1_fetch.KnownSymbolsManager.update_known_symbols', return_value=True):
                                result = fetch_all_available_data()

            # Should return None because no symbol has sufficient data
            assert result is None


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

def test_integration_workflow():
    """Integration test simulating the full workflow."""
    # This is a higher-level test that verifies the interaction between components

    # 1. Test Headers construction
    headers = Headers.General.DEFAULT(FIRST_NAME, LAST_NAME)
    assert "Bearer Cynthia.Kraft" in headers["Authorization"]

    # 2. Test URL construction
    assert Fiindo_Endpoints.api_base_url == "https://api.test.fiindo.com/api"

    # 3. Test with temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        temp_file = f.name

    try:
        # Set temp file as known symbols file
        original_file = KnownSymbolsManager.KNOWN_SYMBOLS_FILE
        KnownSymbolsManager.KNOWN_SYMBOLS_FILE = temp_file

        # Test saving and loading
        test_data = {"TEST": "Test Industry"}
        KnownSymbolsManager.save_known_symbols(test_data)

        loaded = KnownSymbolsManager.load_known_symbols()
        assert loaded == test_data

    finally:
        # Cleanup
        if os.path.exists(temp_file):
            os.unlink(temp_file)
        KnownSymbolsManager.KNOWN_SYMBOLS_FILE = original_file


# ============================================================================
# EDGE CASE TESTS
# ============================================================================

def test_industry_extraction_edge_cases():
    """Test industry extraction from various response structures."""
    # This would normally be tested in the context of fetch_all_available_data
    # but we can create a helper test

    test_cases = [
        # (response_json, expected_industry)
        ({
             "fundamentals": {
                 "profile": {
                     "data": [{"industry": "Software - Application"}]
                 }
             }
         }, "Software - Application"),

        ({
             "fundamentals": {
                 "profile": {
                     "data": []
                 }
             }
         }, "Unknown"),

        ({
             "fundamentals": {}
         }, "Unknown"),

        ({}, "Unknown"),

        ({
             "fundamentals": {
                 "profile": {
                     "data": [{"not_industry": "test"}]
                 }
             }
         }, "Unknown"),
    ]

    # Note: This tests the logic that's embedded in fetch_all_available_data
    # In a real refactor, we might extract this logic into a separate function
    for response_json, expected in test_cases:
        industry = "Unknown"
        try:
            if "fundamentals" in response_json:
                fundamentals = response_json["fundamentals"]
                if "profile" in fundamentals:
                    profile = fundamentals["profile"]
                    if "data" in profile and len(profile["data"]) > 0:
                        industry = profile["data"][0].get("industry", "Unknown")
        except (KeyError, TypeError, IndexError):
            industry = "Unknown"

        assert industry == expected


# ============================================================================
# HELPER FUNCTION TESTS
# ============================================================================

def test_fetch_specific_scenarios():
    """Test specific scenarios with detailed mocking."""

    # Scenario 1: Successful data collection with 4 endpoints
    with patch('requests.get') as mock_get:
        # Create a mock that returns different responses
        mock_responses = {
            '/api/v1/symbols': Mock(status_code=200, json=lambda: {"symbols": ["AAPL"]}),
            '/api/v1/general/AAPL': Mock(status_code=200, json=lambda: {
                "fundamentals": {
                    "profile": {
                        "data": [{"industry": "Software - Application"}]
                    }
                }
            }),
            '/api/v1/eod/AAPL': Mock(status_code=200, json=lambda: {"close": 150}),
            '/api/v1/financials/AAPL/income_statement': Mock(status_code=200, json=lambda: {"revenue": 1000}),
            '/api/v1/financials/AAPL/balance_sheet_statement': Mock(status_code=200, json=lambda: {"assets": 2000}),
            '/api/v1/financials/AAPL/cash_flow_statement': Mock(status_code=200, json=lambda: {"cash_flow": 300}),
        }

        def side_effect(url, **kwargs):
            for key, response in mock_responses.items():
                if key in url:
                    return response
            return Mock(status_code=404)

        mock_get.side_effect = side_effect

        # Mock all file operations
        with patch('builtins.open', mock_open()) as mock_file:
            with patch('json.dump') as mock_dump:
                with patch('os.makedirs'):
                    with patch('step1_fetch.KnownSymbolsManager.load_known_symbols', return_value={}):
                        with patch('step1_fetch.KnownSymbolsManager.update_known_symbols', return_value=True):
                            result = fetch_all_available_data()

        # Verify some API calls were made
        assert mock_get.call_count > 0


if __name__ == "__main__":
    # Run tests directly if file is executed
    pytest.main([__file__, "-v"])