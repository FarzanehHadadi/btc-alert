import os

import requests

BASE_URL = "https://api.telegram.org/bot"
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")


def _request(method: str, **kwargs):
    response = requests.post(
        f"{BASE_URL}{TOKEN}/{method}",
        timeout=10,
        **kwargs,
    )

    response.raise_for_status()

    data = response.json()

    if not data.get("ok"):
        raise RuntimeError(data)

    return data


def get_updates(offset: int = 0):
    return _request(
        "getUpdates",
        json={
            "offset": offset,
            "timeout": 5,
            "allowed_updates": ["message"],
        },
    )["result"]


def send_message(chat_id: int, message: str):
    _request(
        "sendMessage",
        json={
            "chat_id": chat_id,
            "text": message,
        },
    )
