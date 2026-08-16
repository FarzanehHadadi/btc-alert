from coingecko import get_10_day_low, get_btc_price
from dotenv import load_dotenv
from telegram import send_message

load_dotenv()

# THRESHOLD = 0.002
THRESHOLD = 1


def main():
    current_price = get_btc_price()
    ten_day_low = get_10_day_low()

    distance = (current_price - ten_day_low) / ten_day_low

    print(f"Current BTC price: ${current_price:,.2f}")
    print(f"10-day low: ${ten_day_low:,.2f}")
    print(f"Distance: {distance:.2%}")

    if distance <= THRESHOLD:
        send_message(
            f"🚨 BTC Alert!\n\n"
            f"Current: ${current_price:,.2f}\n"
            f"10-day low: ${ten_day_low:,.2f}\n"
            f"Distance: {distance:.2%}"
        )


if __name__ == "__main__":
    main()
