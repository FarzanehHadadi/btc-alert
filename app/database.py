import os
from datetime import datetime, timedelta, timezone

from pymongo import MongoClient, UpdateOne

client = MongoClient(os.getenv("MONGODB_URI"))

db = client["btc_alert"]

market_data = db["market_data"]
ai_analysis = db["ai_analysis"]
subscribers = db["subscribers"]
bot_state = db["bot_state"]

subscribers.create_index(
    [("chat_id", 1)],
    unique=True,
)
market_data.create_index(
    [("symbol", 1), ("timestamp", 1)],
    unique=True,
)


# Market Data Functions
def save_market_data(data: list[dict]):
    if not data:
        return

    operations = [
        UpdateOne(
            {
                "symbol": item["symbol"],
                "timestamp": item["timestamp"],
            },
            {"$set": item},
            upsert=True,
        )
        for item in data
    ]

    market_data.bulk_write(operations)


def get_last_90_days():
    cutoff = (datetime.now(timezone.utc) - timedelta(days=90)).timestamp() * 1000

    return list(
        market_data.find(
            {
                "symbol": "BTC",
                "timestamp": {"$gte": cutoff},
            },
            {"_id": 0},
        ).sort("timestamp", 1)
    )


def save_analysis(data: dict):
    ai_analysis.insert_one(data)


# Telegram Bot Functions
def subscribe(chat_id: int, username: str | None = None):
    subscribers.update_one(
        {"chat_id": chat_id},
        {
            "$set": {
                "chat_id": chat_id,
                "username": username,
                "active": True,
                "updated_at": datetime.now(timezone.utc),
            },
            "$setOnInsert": {
                "created_at": datetime.now(timezone.utc),
            },
        },
        upsert=True,
    )


def unsubscribe(chat_id: int):
    subscribers.update_one(
        {"chat_id": chat_id},
        {
            "$set": {
                "active": False,
                "updated_at": datetime.now(timezone.utc),
            }
        },
    )


def get_active_subscribers():
    return list(
        subscribers.find(
            {"active": True},
            {"_id": 0, "chat_id": 1},
        )
    )


def get_update_offset() -> int:
    state = bot_state.find_one({"key": "telegram_update_offset"})
    return state["value"] if state else 0


def save_update_offset(offset: int):
    bot_state.update_one(
        {"key": "telegram_update_offset"},
        {"$set": {"value": offset}},
        upsert=True,
    )
