# speedboost.py

import requests
import json

#  Daten
FIRST_NAME = "Cynthia"
LAST_NAME = "Kraft"
BEARER_TOKEN = f"{FIRST_NAME}.{LAST_NAME}"


def test_speedboost():
    """Testet den Speed Boost Endpoint"""
    print("=" * 60)
    print("SPEED BOOST TEST")
    print("=" * 60)

    url = "https://api.test.fiindo.com/api/v1/speedboost"
    payload = {
        "first_name": FIRST_NAME,
        "last_name": LAST_NAME
    }

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": f"Bearer {BEARER_TOKEN}"
    }

    print(f"\n📤 Sende Speed Boost Anfrage für: {FIRST_NAME} {LAST_NAME}")
    print(f"🔑 Authorization Header: Bearer {BEARER_TOKEN}")

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)

        print(f"\n📥 Response Status: {response.status_code}")
        print(f"📥 Response Text: {response.text}")

        if response.status_code == 200:
            print("\n✅ Speed Boost aktiviert für 1 Stunde!")

            # Teste eine schnelle API-Anfrage
            print("\n⚡ Teste API-Geschwindigkeit...")
            test_response = requests.get(
                "https://api.test.fiindo.com/health",
                headers={"Authorization": f"Bearer {BEARER_TOKEN}"},
                timeout=10
            )
            print(f"   Health Check: {test_response.status_code} in {test_response.elapsed.total_seconds():.2f}s")

        elif response.status_code == 401:
            print("\n❌ Unauthorized! Prüfen Sie Ihren Namen:")
            print(f"   FIRST_NAME: {FIRST_NAME}")
            print(f"   LAST_NAME: {LAST_NAME}")
            print(f"   BEARER_TOKEN: {BEARER_TOKEN}")

        elif response.status_code == 429:
            print("\n⚠️  Rate Limit erreicht. Warten Sie eine Minute.")

    except Exception as e:
        print(f"\n❌ Fehler: {e}")


if __name__ == "__main__":
    test_speedboost()