from coingecko import get_10_day_low, get_btc_price
from dotenv import load_dotenv
from telegram import send_message

load_dotenv()

LOW_THRESHOLD = 0.002


def main():
    current_price = get_btc_price()
    ten_day_low = get_10_day_low()

    distance = (current_price - ten_day_low) / ten_day_low

    print(f"Current BTC price: ${current_price:,.2f}")
    print(f"10-day low: ${ten_day_low:,.2f}")
    print(f"Distance: {distance:.2%}")

    # Normal hourly update
    message = (
        f"🟢 BTC Hourly Update\n\n"
        f"💰 Current: ${current_price:,.2f}\n"
        f"📉 10D Low: ${ten_day_low:,.2f}\n"
        f"📏 Distance: {distance:.2%}"
    )

    send_message(message)

    # Low alert
    if distance <= LOW_THRESHOLD:
        alert = (
            "🚨🚨🚨 BTC LOW ALERT 🚨🚨🚨\n\n"
            "🟢🟢🟢🟢🟢🟢🟢\n\n"
            f"💰 Current: ${current_price:,.2f}\n"
            f"📉 10D Low: ${ten_day_low:,.2f}\n"
            f"📏 Distance: {distance:.2%}\n\n"
            "⚡ BTC has reached the 10-day low zone.\n"
            "👀 BUY-WATCH SIGNAL"
        )

        send_message(alert)


if __name__ == "__main__":
    main()
