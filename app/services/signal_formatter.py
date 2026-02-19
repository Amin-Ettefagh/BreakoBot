from __future__ import annotations

from app.services.analysis import AnalysisResult


def naive_entry_tp_sl(last_close: float) -> tuple[float, list[float], float]:
    """Simple TP/SL generator for MVP signals."""
    entry = last_close
    tps = [entry * 1.005, entry * 1.01, entry * 1.015]
    sl = entry * 0.995
    return entry, tps, sl


def format_spot_signal(
    result: AnalysisResult, entry: float, tp_list: list[float], sl: float
) -> str:
    lines = [
        f"{result.symbol} - SPOT SIGNAL",
        f"Entry: {entry:.6f}",
    ]
    for i, tp in enumerate(tp_list, start=1):
        lines.append(f"TP{i}: {tp:.6f}")
    lines.append(f"SL: {sl:.6f}")
    lines.append("")
    lines.append(result.to_text())
    lines.append("---------------------------")
    return "\n".join(lines)


def format_breakout_signal(symbol: str, last_close: float, prev_high: float, lookback: int) -> str:
    return (
        "FUTURES BREAKOUT\n"
        f"Symbol: {symbol}\n"
        f"Last Close: {last_close:.6f}\n"
        f"Prev High({lookback}): {prev_high:.6f}"
    )
