import requests


BASE_URL = "https://api.binance.com"


def get_btc_price() -> float:
    response = requests.get(
        f"{BASE_URL}/api/v3/ticker/price",
        params={"symbol": "BTCUSDT"},
        timeout=10,
    )
    response.raise_for_status()

    return float(response.json()["price"])


def get_10_day_low() -> float:
    response = requests.get(
        f"{BASE_URL}/api/v3/klines",
        params={
            "symbol": "BTCUSDT",
            "interval": "1d",
            "limit": 10,
        },
        timeout=10,
    )
    response.raise_for_status()

    candles = response.json()

    lows = [float(candle[3]) for candle in candles]

    return min(lows)
