import requests

BASE_URL = "https://api.coingecko.com/api/v3"


def get_btc_price() -> float:
    response = requests.get(
        f"{BASE_URL}/simple/price",
        params={
            "ids": "bitcoin",
            "vs_currencies": "usd",
        },
        timeout=10,
    )
    response.raise_for_status()

    return float(response.json()["bitcoin"]["usd"])


def get_10_day_low() -> float:
    response = requests.get(
        f"{BASE_URL}/coins/bitcoin/market_chart",
        params={
            "vs_currency": "usd",
            "days": 10,
            "interval": "daily",
        },
        timeout=10,
    )
    response.raise_for_status()

    prices = response.json()["prices"]

    return min(price for _, price in prices)
