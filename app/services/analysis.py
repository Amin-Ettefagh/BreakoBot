from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

import numpy as np
import pandas as pd

from app.db.database import Database
from app.services.mexc_api import MexcClient


def calculate_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = (-delta).clip(lower=0)
    avg_gain = gain.rolling(period, min_periods=period).mean()
    avg_loss = loss.rolling(period, min_periods=period).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    return rsi.bfill().fillna(50)


def calculate_ema(series: pd.Series, period: int) -> pd.Series:
    return series.ewm(span=period, adjust=False).mean()


def calculate_macd(
    series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9
) -> Tuple[pd.Series, pd.Series]:
    ema_fast = series.ewm(span=fast, adjust=False).mean()
    ema_slow = series.ewm(span=slow, adjust=False).mean()
    macd = ema_fast - ema_slow
    sig = macd.ewm(span=signal, adjust=False).mean()
    return macd, sig


def detect_breakout(df: pd.DataFrame, lookback: int = 2) -> bool:
    if len(df) < lookback + 1:
        return False
    last_close = float(df["close"].iloc[-1])
    prev_high = float(df["high"].iloc[-(lookback + 1) : -1].max())
    return last_close > prev_high


@dataclass
class AnalysisResult:
    symbol: str
    interval: str
    last_close: float
    rsi: float
    ema20: float
    ema50: float
    macd: float
    macd_signal: float
    volume: float
    breakout: bool

    def to_text(self) -> str:
        lines = [
            f"Analysis {self.symbol} ({self.interval})",
            f"Close: {self.last_close:.6f}",
            f"RSI: {self.rsi:.2f}",
            f"EMA20: {self.ema20:.6f} | EMA50: {self.ema50:.6f}",
            f"MACD: {self.macd:.6f} | Signal: {self.macd_signal:.6f}",
            f"Volume: {self.volume:.2f}",
            "Breakout detected" if self.breakout else "No breakout",
        ]
        return "\n".join(lines)


async def analyze_coin(
    symbol: str, interval: str, mexc: MexcClient, db: Database
) -> AnalysisResult:
    """Fetch candles, compute indicators, and persist cache."""
    raw = await mexc.get_candles(symbol, interval, limit=120)
    if not raw:
        raise RuntimeError(f"No candles for {symbol}")

    df = pd.DataFrame(raw)
    df["close"] = df["close"].astype(float)

    df["rsi"] = calculate_rsi(df["close"])
    df["ema20"] = calculate_ema(df["close"], 20)
    df["ema50"] = calculate_ema(df["close"], 50)
    df["macd"], df["macd_signal"] = calculate_macd(df["close"])

    last_close = float(df["close"].iloc[-1])
    last_volume = float(df["volume"].iloc[-1])
    breakout = detect_breakout(df, lookback=2)

    res = AnalysisResult(
        symbol=symbol,
        interval=interval,
        last_close=last_close,
        rsi=float(df["rsi"].iloc[-1]),
        ema20=float(df["ema20"].iloc[-1]),
        ema50=float(df["ema50"].iloc[-1]),
        macd=float(df["macd"].iloc[-1]),
        macd_signal=float(df["macd_signal"].iloc[-1]),
        volume=last_volume,
        breakout=breakout,
    )

    await db.upsert_analysis_cache(
        symbol,
        res.rsi,
        res.macd,
        res.ema20,
        res.ema50,
        res.volume,
        res.breakout,
    )
    return res
