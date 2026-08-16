import os

import requests

BASE_URL = "https://api.coingecko.com/api/v3"


def get_90_days_data() -> list[dict]:
    response = requests.get(
        f"{BASE_URL}/coins/bitcoin/market_chart",
        params={
            "vs_currency": "usd",
            "days": 90,
            "interval": "hourly",
        },
        headers={
            "x-cg-demo-api-key": os.getenv("COINGECKO_API_KEY"),
        },
        timeout=20,
    )

    response.raise_for_status()

    data = response.json()

    prices = data["prices"]
    volumes = data["total_volumes"]

    volume_map = {timestamp: volume for timestamp, volume in volumes}

    return [
        {
            "symbol": "BTC",
            "timestamp": timestamp,
            "price": price,
            "volume": volume_map.get(timestamp),
        }
        for timestamp, price in prices
    ]
