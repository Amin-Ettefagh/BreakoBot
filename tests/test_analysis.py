import pandas as pd
from app.services.analysis import calculate_ema, calculate_macd, calculate_rsi, detect_breakout


def test_rsi_constant_series():
    series = pd.Series([1.0] * 30)
    rsi = calculate_rsi(series)
    assert float(rsi.iloc[-1]) == 50.0


def test_ema_constant_series():
    series = pd.Series([2.0] * 10)
    ema = calculate_ema(series, 5)
    assert float(ema.iloc[-1]) == 2.0


def test_macd_constant_series():
    series = pd.Series([3.0] * 40)
    macd, signal = calculate_macd(series)
    assert abs(float(macd.iloc[-1])) < 1e-6
    assert abs(float(signal.iloc[-1])) < 1e-6


def test_detect_breakout():
    df = pd.DataFrame(
        {
            "close": [1, 2, 3, 4],
            "high": [1, 2, 3, 3.5],
        }
    )
    assert detect_breakout(df, lookback=2) is True

    df2 = pd.DataFrame(
        {
            "close": [1, 2, 2.5, 2.9],
            "high": [1, 2, 3, 3.2],
        }
    )
    assert detect_breakout(df2, lookback=2) is False
