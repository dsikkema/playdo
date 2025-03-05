"""
Just do two basic requests to verify successful, non-empty responses
"""

import requests  # type: ignore


def main():
    # verify 200 status
    response = requests.get("http://localhost:5000/api/conversations")
    assert response.status_code == 200
    assert response.json() is not None

    response = requests.get("http://localhost:5000/api/conversations/1")
    assert response.status_code == 200
    assert response.json() is not None
    print("✅")


if __name__ == "__main__":
    main()
