import os
from typing import Literal

from google import genai
from pydantic import BaseModel, Field

MODEL = "gemini-3.1-flash-lite"

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


class StrategyAnalysis(BaseModel):
    score: int = Field(ge=0, le=100)
    satisfied: bool
    why: str
    invalidating_conditions: list[str]


class TradeSignal(BaseModel):
    signal: Literal["BUY", "SELL", "WATCH", "WAIT"]
    target_price: float | None = None
    invalidation_price: float | None = None
    rationale: str


class AIAnalysis(BaseModel):
    mean_reversion: StrategyAnalysis
    trend_following: StrategyAnalysis
    momentum: StrategyAnalysis
    support_resistance: StrategyAnalysis
    volatility_breakout: StrategyAnalysis

    overall_score: int = Field(ge=0, le=100)
    assessment: str
    confidence: float = Field(ge=0, le=1)
    trade_signal: TradeSignal

    reasons: list[str]
    risks: list[str]


def analyze_market(features: dict, llm_data: list[dict]) -> AIAnalysis:
    prompt = f"""
    You are analyzing Bitcoin market conditions.

    You have:
    1. 90 days of daily aggregated BTC price data.
    2. The most recent 7 days of hourly BTC price and volume data.
    3. Calculated market features.

    Important:
    - Daily OHLC values are derived from hourly price observations, not exchange-native OHLC candles.
    - Use only the provided data.
    - Do not invent indicators, prices, volume, support levels, or events.
    - Do not assume information that is not present in the data.
    - Treat this as market analysis, not guaranteed financial advice.

    Current market features:
    {features}

    Market data:
    {llm_data}

    Evaluate these strategies:

    1. Mean Reversion
    2. Trend Following
    3. Momentum
    4. Support/Resistance
    5. Volatility Breakout

    For each strategy:
    - determine whether current conditions satisfy it
    - score 0-100
    - explain why
    - identify invalidating conditions

    Then produce an overall assessment:
    BUY / WATCH / WAIT

    Consider conflicting signals and downside risk.
    After evaluating the five strategies, produce an overall trading assessment.

    The assessment must be one of:
    BUY
    SELL
    WATCH
    WAIT

    If the assessment is BUY:
    - provide a realistic upside target price based only on the supplied data
    - provide an invalidation price below the current price
    - explain the reasoning for the target

    If the assessment is SELL:
    - provide a realistic downside target price based only on the supplied data
    - provide an invalidation price above the current price
    - explain the reasoning for the target

    If the assessment is WATCH or WAIT:
    - target_price may be null
    - invalidation_price may be null

    Do not invent exact support/resistance levels.
    Do not claim that price will definitely reach the target.
    Targets must be derived from the supplied historical market data.
    """

    response = client.models.generate_content(
        model=MODEL,
        contents=prompt,
        config={
            "response_mime_type": "application/json",
            "response_schema": AIAnalysis.model_json_schema(),
        },
    )

    return AIAnalysis.model_validate_json(response.text)


def validate_trade_signal(result: AIAnalysis, current_price: float):
    signal = result.trade_signal

    if signal.signal == "BUY":
        if (
            signal.target_price is None
            or signal.invalidation_price is None
            or signal.target_price <= current_price
            or signal.invalidation_price >= current_price
        ):
            raise ValueError("Invalid BUY trade signal")

    elif signal.signal == "SELL" and (
        signal.target_price is None
        or signal.invalidation_price is None
        or signal.target_price >= current_price
        or signal.invalidation_price <= current_price
    ):
        raise ValueError("Invalid SELL trade signal")
