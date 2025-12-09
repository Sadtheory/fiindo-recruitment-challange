# speedboost.py

import requests
import json

# Data for the speed boost request
# Using first and last name to construct the Bearer token
FIRST_NAME = "Cynthia"
LAST_NAME = "Kraft"
# Bearer token is formed by combining first and last name with a dot
BEARER_TOKEN = f"{FIRST_NAME}.{LAST_NAME}"


def test_speedboost():
    """Tests the Speed Boost endpoint to activate high-speed API access for one hour."""
    print("=" * 60)
    print("SPEED BOOST TEST")
    print("=" * 60)

    # API endpoint for activating speed boost
    url = "https://api.test.fiindo.com/api/v1/speedboost"

    # Payload containing user identification data
    payload = {
        "first_name": FIRST_NAME,
        "last_name": LAST_NAME
    }

    # HTTP headers including authorization with Bearer token
    headers = {
        "Content-Type": "application/json",  # Indicates JSON content
        "Accept": "application/json",  # Expects JSON response
        "Authorization": f"Bearer {BEARER_TOKEN}"  # Authentication header
    }

    print(f"\n📤 Sending Speed Boost request for: {FIRST_NAME} {LAST_NAME}")
    print(f"🔑 Authorization Header: Bearer {BEARER_TOKEN}")

    try:
        # Send POST request to activate speed boost
        response = requests.post(url, json=payload, headers=headers, timeout=30)

        print(f"\n📥 Response Status: {response.status_code}")
        print(f"📥 Response Text: {response.text}")

        # Check response status code
        if response.status_code == 200:
            print("\n✅ Speed Boost activated for 1 hour!")

            # Test API speed with a simple health check request
            print("\n⚡ Testing API speed...")
            test_response = requests.get(
                "https://api.test.fiindo.com/health",  # Health check endpoint
                headers={"Authorization": f"Bearer {BEARER_TOKEN}"},
                timeout=10
            )
            # Display response time to verify speed improvement
            print(f"   Health Check: {test_response.status_code} in {test_response.elapsed.total_seconds():.2f}s")

        elif response.status_code == 401:
            print("\n❌ Unauthorized! Please check your name:")
            print(f"   FIRST_NAME: {FIRST_NAME}")
            print(f"   LAST_NAME: {LAST_NAME}")
            print(f"   BEARER_TOKEN: {BEARER_TOKEN}")

        elif response.status_code == 429:
            print("\n⚠️  Rate limit reached. Please wait one minute.")

    except Exception as e:
        print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    test_speedboost()