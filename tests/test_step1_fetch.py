# tests/test_step1_fetch.py
import sys
import os

# Füge src Verzeichnis zum Python-Pfad hinzu
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
src_dir = os.path.join(parent_dir, 'src')
sys.path.insert(0, src_dir)

# Importiere aus src.step1
from step1 import (
    Fiindo_Endpoints,
    Headers,
    fetch_all_available_data,
    FIRST_NAME,
    LAST_NAME
)


def test_step1_import():
    """Test dass step1 korrekt importiert werden kann"""
    print("Testing Step 1 import...")

    # Prüfe wichtige Komponenten
    assert Fiindo_Endpoints is not None
    assert Headers is not None
    assert fetch_all_available_data is not None

    # Prüfe API Credentials
    assert FIRST_NAME == "Cynthia"
    assert LAST_NAME == "Kraft"

    print("✅ Step 1 import successful")
    return True


def test_headers_class():
    """Test der Headers Klasse"""
    print("Testing Headers class...")

    # Test Auth Header
    headers = Headers.General.Auth("John", "Doe")
    assert headers == {"Authorization": "Bearer John.Doe"}

    # Test Accept Header
    headers = Headers.General.Accept()
    assert headers == {"Accept": "text/plain"}

    print("✅ Headers class works correctly")
    return True


def test_fiindo_endpoints_structure():
    """Test der Fiindo Endpoints Struktur"""
    print("Testing Fiindo Endpoints structure...")

    # Prüfe Basis-URL
    assert Fiindo_Endpoints.api_base_url == "https://api.test.fiindo.com/api"
    assert Fiindo_Endpoints.api_version == "v1"

    # Prüfe Endpoint-Klassen
    assert hasattr(Fiindo_Endpoints, 'Financials')
    assert hasattr(Fiindo_Endpoints, 'General')
    assert hasattr(Fiindo_Endpoints, 'Symbols')

    print("✅ Fiindo Endpoints structure is correct")
    return True


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("Running Step 1 Tests (test_step1_fetch.py)")
    print("=" * 60 + "\n")

    tests = [
        test_step1_import,
        test_headers_class,
        test_fiindo_endpoints_structure
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ {test.__name__} failed: {e}")

    print(f"\n{'=' * 60}")
    print(f"Results: {passed}/{total} tests passed")
    if passed == total:
        print("🎉 All Step 1 tests completed successfully!")
    else:
        print(f"⚠️  {total - passed} test(s) failed")
    print('=' * 60)