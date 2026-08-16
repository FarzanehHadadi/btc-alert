from collections import defaultdict
from datetime import datetime, timezone
from statistics import mean, pstdev


def calculate_features(data: list[dict]) -> dict:
    prices = [item["price"] for item in data]
    volumes = [item["volume"] for item in data if item.get("volume") is not None]

    current_price = prices[-1]

    high_90d = max(prices)
    low_90d = min(prices)

    change_30d = 0.0
    if len(prices) >= 24 * 30:
        price_30d_ago = prices[-24 * 30]
        change_30d = (current_price - price_30d_ago) / price_30d_ago

    change_7d = 0.0
    if len(prices) >= 24 * 7:
        price_7d_ago = prices[-24 * 7]
        change_7d = (current_price - price_7d_ago) / price_7d_ago

    returns = [
        (prices[i] - prices[i - 1]) / prices[i - 1] for i in range(1, len(prices))
    ]

    volatility = pstdev(returns) if returns else 0.0

    volume_change = 0.0

    if len(volumes) >= 48:
        recent_volume = mean(volumes[-24:])
        previous_volume = mean(volumes[-48:-24])

        if previous_volume:
            volume_change = (recent_volume - previous_volume) / previous_volume

    distance_from_low = (current_price - low_90d) / low_90d

    distance_from_high = (high_90d - current_price) / high_90d

    return {
        "current_price": current_price,
        "high_90d": high_90d,
        "low_90d": low_90d,
        "change_7d": change_7d,
        "change_30d": change_30d,
        "volatility": volatility,
        "volume_change": volume_change,
        "distance_from_low": distance_from_low,
        "distance_from_high": distance_from_high,
    }


def is_interesting(features: dict) -> bool:
    return any(
        [
            features["distance_from_low"] <= 0.05,
            features["distance_from_high"] <= 0.05,
            abs(features["change_7d"]) >= 0.08,
            abs(features["change_30d"]) >= 0.15,
            features["volume_change"] >= 0.50,
        ]
    )


def prepare_llm_data(data: list[dict]) -> dict:
    daily = defaultdict(list)

    for item in data:
        dt = datetime.fromtimestamp(
            item["timestamp"] / 1000,
            tz=timezone.utc,
        )

        day = dt.date().isoformat()

        daily[day].append(item)

    daily_data = []

    for day, items in sorted(daily.items()):
        prices = [item["price"] for item in items]

        volumes = [item["volume"] for item in items if item.get("volume") is not None]

        daily_data.append(
            {
                "date": day,
                "open": round(prices[0], 2),
                "high": round(max(prices), 2),
                "low": round(min(prices), 2),
                "close": round(prices[-1], 2),
                "volume": round(sum(volumes), 2),
            }
        )

    recent_hourly = [
        {
            "timestamp": item["timestamp"],
            "price": round(item["price"], 2),
            "volume": round(item["volume"], 2)
            if item.get("volume") is not None
            else None,
        }
        for item in data[-24 * 7 :]
    ]

    return {
        "daily_90d": daily_data,
        "recent_7d_hourly": recent_hourly,
    }
