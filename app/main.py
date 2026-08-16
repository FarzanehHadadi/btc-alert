from dotenv import load_dotenv

load_dotenv()

from analysis import calculate_features, is_interesting
from coingecko import get_90_days_data
from database import (
    get_active_subscribers,
    get_last_90_days,
    get_update_offset,
    save_market_data,
    save_update_offset,
    subscribe,
    unsubscribe,
)
from telegram import get_updates, send_message


def process_telegram_updates():
    offset = get_update_offset()
    updates = get_updates(offset)

    for update in updates:
        update_id = update["update_id"]

        message = update.get("message")

        if message:
            chat = message["chat"]
            chat_id = chat["id"]
            username = chat.get("username")
            text = message.get("text", "").strip()

            if text == "/start":
                subscribe(chat_id, username)

                send_message(
                    chat_id,
                    "✅ You are subscribed to BTC alerts.",
                )

            elif text == "/stop":
                unsubscribe(chat_id)

                send_message(
                    chat_id,
                    "🛑 You are unsubscribed from BTC alerts.",
                )

        save_update_offset(update_id + 1)


def broadcast_message(message: str):
    subscribers = get_active_subscribers()

    for subscriber in subscribers:
        chat_id = subscriber["chat_id"]

        try:
            send_message(chat_id, message)
        except Exception as exc:
            print(f"Failed to send message to {chat_id}: {exc}")


def main():
    process_telegram_updates()
    # Update market data
    data = get_90_days_data()

    print(f"Received {len(data)} records from CoinGecko")

    save_market_data(data)

    # Read stored 90-day dataset
    historical_data = get_last_90_days()

    print(f"Loaded {len(historical_data)} records from MongoDB")

    features = calculate_features(historical_data)

    print("\nMarket features:")
    for key, value in features.items():
        if isinstance(value, float):
            print(f"{key}: {value:.4f}")
        else:
            print(f"{key}: {value}")

    interesting = is_interesting(features)

    print(f"\nInteresting market: {interesting}")

    if interesting:
        message = (
            "🧠 BTC MARKET ALERT\n\n"
            f"💰 Price: ${features['current_price']:,.2f}\n"
            f"📉 90D Low: ${features['low_90d']:,.2f}\n"
            f"📈 90D High: ${features['high_90d']:,.2f}\n"
            f"📊 7D Change: {features['change_7d']:.2%}\n"
            f"📊 30D Change: {features['change_30d']:.2%}\n\n"
            "🤖 Market conditions are interesting.\n"
            "AI analysis will be triggered."
        )
    else:
        message = (
            "🟢 BTC HOURLY UPDATE\n\n"
            f"💰 Price: ${features['current_price']:,.2f}\n"
            f"📉 90D Low: ${features['low_90d']:,.2f}\n"
            f"📈 90D High: ${features['high_90d']:,.2f}\n"
            f"📊 7D Change: {features['change_7d']:.2%}\n"
            f"📊 30D Change: {features['change_30d']:.2%}\n\n"
            "No significant market setup detected."
        )

    broadcast_message(message)


if __name__ == "__main__":
    main()
