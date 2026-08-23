from dotenv import load_dotenv

load_dotenv()
from datetime import datetime, timezone

from analysis import (
    calculate_features,
    is_interesting,
    prepare_llm_data,
)
from coingecko import get_90_days_data
from database import (
    get_active_subscribers,
    get_last_90_days,
    get_update_offset,
    save_analysis,
    save_market_data,
    save_update_offset,
    subscribe,
    unsubscribe,
)
from gemini import analyze_market, validate_trade_signal
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


def format_ai_message(result, price: float) -> str:
    signal_icons = {
        "BUY": "🟢🟢🟢",
        "SELL": "🔴🔴🔴",
        "WATCH": "🟡",
        "WAIT": "⚪",
    }
    icon = signal_icons.get(result.assessment, "⚪")

    message = (
        f"{icon} BTC AI ANALYSIS\n\n"
        f"💰 Price: ${price:,.2f}\n\n"
        f"📌 Assessment: {result.assessment}\n"
        "📊 Strategies\n\n"
        f"↩️ Mean Reversion: {result.mean_reversion.score}/100\n"
        f"📈 Trend Following: {result.trend_following.score}/100\n"
        f"⚡ Momentum: {result.momentum.score}/100\n"
        f"📍 Support/Resistance: {result.support_resistance.score}/100\n"
        f"💥 Volatility Breakout: {result.volatility_breakout.score}/100\n\n"
        f"🎯 Overall: {result.overall_score}/100\n"
        f"🤖 Confidence: {result.confidence:.0%}\n"
    )

    signal = result.trade_signal

    if signal.signal in ("BUY", "SELL"):
        message += (
            "\n━━━━━━━━━━━━━━\n\n"
            f"{'🟢' if signal.signal == 'BUY' else '🔴'} "
            f"Signal: {signal.signal}\n"
            f"🎯 Target: ${signal.target_price:,.2f}\n"
            f"🛑 Invalidation: ${signal.invalidation_price:,.2f}\n"
            f"📌 {signal.rationale}\n"
        )

    message += (
        "\n📌 Reasons:\n"
        + "\n".join(f"• {item}" for item in result.reasons)
        + "\n\n⚠️ Risks:\n"
        + "\n".join(f"• {item}" for item in result.risks)
    )

    return message


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
    ai_result = None

    if interesting:
        llm_data = prepare_llm_data(historical_data)

        try:
            ai_result = analyze_market(
                features,
                llm_data,
            )
            validate_trade_signal(
                ai_result,
                features["current_price"],
            )

            print("\nAI Analysis:")
            print(ai_result.model_dump_json(indent=2))

        except Exception as exc:
            print(f"Gemini analysis failed: {exc}")

    if ai_result:
        save_analysis(
            {
                "timestamp": datetime.now(timezone.utc),
                "price": features["current_price"],
                **ai_result.model_dump(),
            }
        )
        message = format_ai_message(
            ai_result,
            features["current_price"],
        )
    else:
        message = (
            "🟢 BTC HOURLY UPDATE\n\n"
            "No significant market setup detected."
            f"💰 Price: ${features['current_price']:,.2f}\n"
            f"📉 90D Low: ${features['low_90d']:,.2f}\n"
            f"📈 90D High: ${features['high_90d']:,.2f}\n"
            f"📊 7D Change: {features['change_7d']:.2%}\n"
            f"📊 30D Change: {features['change_30d']:.2%}\n"
            f"📉 Distance from 90D Low: "
            f"{features['distance_from_low']:.2%}\n\n"
        )

    broadcast_message(message)


if __name__ == "__main__":
    main()
