"""
Computes all trading performance statistics from a normalized trade
DataFrame (as produced by parser.py). Every function here takes a
DataFrame and returns plain Python types / small DataFrames — no
plotting or formatting happens in this module, so the numbers can be
tested independently of how they're displayed.
"""

from __future__ import annotations

import pandas as pd
import numpy as np


SESSION_BOUNDS = [
    (0, 7, "Asia"),
    (7, 12, "London"),
    (12, 17, "NY / Overlap"),
    (17, 24, "Late NY"),
]


def assign_session(hour: int) -> str:
    for start, end, name in SESSION_BOUNDS:
        if start <= hour < end:
            return name
    return "Unknown"


def enrich(df: pd.DataFrame) -> pd.DataFrame:
    """Add derived columns used across multiple stat functions, so this
    only has to be computed once."""
    df = df.copy()
    df["is_win"] = df["profit"] > 0
    df["net"] = df["profit"] + df["commission"] + df["swap"]
    df["session"] = df["open_time"].dt.hour.apply(assign_session)
    df["day_of_week"] = df["open_time"].dt.day_name()
    df["month"] = df["open_time"].dt.to_period("M").astype(str)
    df["cumulative_net"] = df["net"].cumsum()
    return df


def overview_stats(df: pd.DataFrame) -> dict:
    total_trades = len(df)
    wins = df[df["is_win"]]
    losses = df[~df["is_win"]]

    win_rate = len(wins) / total_trades * 100 if total_trades else 0
    gross_profit = wins["net"].sum()
    gross_loss = losses["net"].sum()  # negative
    net_profit = df["net"].sum()

    profit_factor = (gross_profit / abs(gross_loss)) if gross_loss != 0 else float("inf")
    avg_win = wins["net"].mean() if len(wins) else 0
    avg_loss = losses["net"].mean() if len(losses) else 0
    expectancy = (win_rate / 100 * avg_win) + ((1 - win_rate / 100) * avg_loss)
    avg_rr = abs(avg_win / avg_loss) if avg_loss else float("inf")

    return {
        "total_trades": total_trades,
        "win_rate": round(win_rate, 1),
        "net_profit": round(net_profit, 2),
        "gross_profit": round(gross_profit, 2),
        "gross_loss": round(gross_loss, 2),
        "profit_factor": round(profit_factor, 2) if profit_factor != float("inf") else None,
        "avg_win": round(avg_win, 2),
        "avg_loss": round(avg_loss, 2),
        "avg_rr": round(avg_rr, 2) if avg_rr != float("inf") else None,
        "expectancy": round(expectancy, 2),
        "start_date": df["open_time"].min().strftime("%Y-%m-%d"),
        "end_date": df["open_time"].max().strftime("%Y-%m-%d"),
    }


def drawdown_stats(df: pd.DataFrame) -> dict:
    """Max drawdown as a currency amount off the running peak of cumulative
    net P/L, plus how many trades it took to recover (or 'ongoing' if the
    equity curve never regained the prior peak)."""
    cum = df["cumulative_net"].values
    running_max = np.maximum.accumulate(cum)
    drawdown = cum - running_max
    max_dd_idx = int(np.argmin(drawdown)) if len(drawdown) else 0
    max_dd = float(drawdown[max_dd_idx]) if len(drawdown) else 0.0

    # Duration: trades between the peak that preceded the max drawdown and
    # the point equity recovers back to that peak (or end of data).
    if len(drawdown):
        peak_value = running_max[max_dd_idx]
        recovery_idx = next(
            (i for i in range(max_dd_idx, len(cum)) if cum[i] >= peak_value), None
        )
        duration = (recovery_idx - max_dd_idx) if recovery_idx is not None else (len(cum) - 1 - max_dd_idx)
        recovered = recovery_idx is not None
    else:
        duration = 0
        recovered = True

    return {
        "max_drawdown": round(max_dd, 2),
        "max_drawdown_duration_trades": int(duration),
        "recovered": recovered,
    }


def streak_stats(df: pd.DataFrame) -> dict:
    longest_win = longest_loss = current = 0
    current_type = None
    for is_win in df["is_win"]:
        if is_win == current_type:
            current += 1
        else:
            current_type = is_win
            current = 1
        if is_win:
            longest_win = max(longest_win, current)
        else:
            longest_loss = max(longest_loss, current)

    return {"longest_win_streak": longest_win, "longest_loss_streak": longest_loss}


def _breakdown(df: pd.DataFrame, group_col: str) -> pd.DataFrame:
    grouped = df.groupby(group_col).agg(
        trades=("net", "count"),
        win_rate=("is_win", lambda s: round(s.mean() * 100, 1)),
        net_profit=("net", lambda s: round(s.sum(), 2)),
    ).reset_index()
    return grouped.sort_values("net_profit", ascending=False)


def breakdown_by_session(df: pd.DataFrame) -> pd.DataFrame:
    order = [name for _, _, name in SESSION_BOUNDS]
    result = _breakdown(df, "session")
    result["session"] = pd.Categorical(result["session"], categories=order, ordered=True)
    return result.sort_values("session")


def breakdown_by_symbol(df: pd.DataFrame) -> pd.DataFrame:
    return _breakdown(df, "symbol")


def breakdown_by_day_of_week(df: pd.DataFrame) -> pd.DataFrame:
    order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    result = _breakdown(df, "day_of_week")
    result["day_of_week"] = pd.Categorical(result["day_of_week"], categories=order, ordered=True)
    return result.sort_values("day_of_week")


def breakdown_by_month(df: pd.DataFrame) -> pd.DataFrame:
    return _breakdown(df, "month").sort_values("month")


def breakdown_by_setup(df: pd.DataFrame) -> pd.DataFrame:
    """Groups by the free-text 'comment' field, treating it as a setup tag.
    Rows with an empty comment are excluded, since they carry no setup info."""
    tagged = df[df["comment"].str.strip() != ""]
    if tagged.empty:
        return pd.DataFrame(columns=["comment", "trades", "win_rate", "net_profit"])
    return _breakdown(tagged, "comment").rename(columns={"comment": "setup"})


def compute_all(df: pd.DataFrame) -> dict:
    """Runs the full pipeline and returns everything a report needs."""
    df = enrich(df)
    return {
        "overview": overview_stats(df),
        "drawdown": drawdown_stats(df),
        "streaks": streak_stats(df),
        "by_session": breakdown_by_session(df),
        "by_symbol": breakdown_by_symbol(df),
        "by_day_of_week": breakdown_by_day_of_week(df),
        "by_month": breakdown_by_month(df),
        "by_setup": breakdown_by_setup(df),
        "equity_curve": df[["open_time", "cumulative_net"]].copy(),
        "trade_log": df[["open_time", "symbol", "type", "net", "session", "comment", "is_win"]].copy(),
    }
