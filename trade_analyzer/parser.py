"""
Parses a trade history from either a CSV file or an HTML statement export
from any trading platform (MT4/MT5, cTrader, Binance, TradingView, or a
generic broker export), and normalizes it into a single pandas DataFrame
with a consistent schema regardless of the input format or exact column
names used. This is the "any CSV or HTML someone hands us" layer — real
broker exports vary widely, so this matches column names loosely rather
than expecting one exact header row.
"""

from __future__ import annotations

import re
import io
import pandas as pd
from bs4 import BeautifulSoup
from pathlib import Path

# Canonical field -> list of substrings that indicate a column is that field.
# Matching is case-insensitive and ignores spaces/punctuation, so "S / L",
# "sl", "Stop Loss" all resolve to the same canonical field. Covers the
# column naming conventions of MT4/MT5, cTrader, Binance, TradingView, and
# generic broker CSV/HTML exports — not any one platform specifically.
COLUMN_ALIASES: dict[str, list[str]] = {
    "open_time": [
        "opentime", "entrytime", "entrydate", "opendate", "starttime",
        "datetime", "date", "time",
    ],
    "close_time": [
        "closetime", "exittime", "exitdate", "closedate", "endtime",
        "time.1", "timeclose", "date.1",
    ],
    "symbol": [
        "symbol", "item", "instrument", "pair", "ticker", "asset", "market",
    ],
    "type": [
        "type", "direction", "side", "tradeside", "action", "buysell", "positiontype",
    ],
    "volume": [
        "volume", "lots", "size", "quantity", "qty", "units", "contracts", "amount",
    ],
    "open_price": [
        "openprice", "entryprice", "entry", "price",
    ],
    "close_price": [
        "closeprice", "exitprice", "exit", "closingprice", "price.1",
    ],
    "sl": ["sl", "stoploss", "stop"],
    "tp": ["tp", "takeprofit", "target"],
    "commission": ["commission", "fee", "fees"],
    "swap": ["swap", "rollover", "financing"],
    "profit": [
        "profit", "pnl", "pl", "netprofit", "realizedpnl", "realizedprofit",
        "p&l", "grossprofit", "result", "gainloss",
    ],
    "comment": ["comment", "note", "notes", "tag", "tags", "strategy", "setup", "label"],
}

# Normalizes the many ways a trade direction gets written across platforms
# (MT5 uses "buy"/"sell", many others use "long"/"short" or single letters)
# into the two canonical values the rest of the pipeline expects.
TYPE_ALIASES: dict[str, str] = {
    "buy": "buy", "long": "buy", "b": "buy", "l": "buy", "1": "buy",
    "sell": "sell", "short": "sell", "s": "sell", "-1": "sell",
}

REQUIRED_FIELDS = ["open_time", "symbol", "type", "profit"]


def _normalize_key(s: str) -> str:
    return re.sub(r"[^a-z0-9.]", "", s.lower())


def _map_columns(columns: list[str]) -> dict[str, str]:
    """Return {canonical_field: original_column_name} for whatever fields
    could be confidently matched. Each canonical field claims at most one
    column, in alias-priority order, and each original column is used once."""
    normalized = {col: _normalize_key(col) for col in columns}
    used_columns: set[str] = set()
    mapping: dict[str, str] = {}

    for field, aliases in COLUMN_ALIASES.items():
        for alias in aliases:
            match = next(
                (col for col, norm in normalized.items()
                 if norm == alias and col not in used_columns),
                None,
            )
            if match:
                mapping[field] = match
                used_columns.add(match)
                break

    return mapping


def _finalize(df: pd.DataFrame, mapping: dict[str, str], source: str) -> pd.DataFrame:
    missing = [f for f in REQUIRED_FIELDS if f not in mapping]
    if missing:
        raise ValueError(
            f"Could not find columns for: {', '.join(missing)}. "
            f"Detected columns were: {list(df.columns)}. "
            "This file may not be a standard trade history export."
        )

    out = pd.DataFrame()
    for field, col in mapping.items():
        out[field] = df[col]

    # Fill any fields that weren't found with sensible defaults so the rest
    # of the pipeline can rely on every column existing.
    for field in COLUMN_ALIASES:
        if field not in out.columns:
            out[field] = "" if field in ("comment", "type", "symbol") else 0.0

    out["open_time"] = pd.to_datetime(out["open_time"], errors="coerce", format="mixed")
    out["close_time"] = pd.to_datetime(out.get("close_time"), errors="coerce", format="mixed")
    out["profit"] = pd.to_numeric(out["profit"], errors="coerce")
    out["volume"] = pd.to_numeric(out["volume"], errors="coerce")
    out["commission"] = pd.to_numeric(out["commission"], errors="coerce").fillna(0)
    out["swap"] = pd.to_numeric(out["swap"], errors="coerce").fillna(0)
    out["type"] = out["type"].astype(str).str.strip().str.lower()
    out["type"] = out["type"].map(lambda v: TYPE_ALIASES.get(v, v))
    out["symbol"] = out["symbol"].astype(str).str.strip()
    out["comment"] = out["comment"].astype(str).str.strip()

    out = out.dropna(subset=["open_time", "profit"])
    out = out[out["type"].isin(["buy", "sell"])]
    out = out.sort_values("open_time").reset_index(drop=True)

    if out.empty:
        raise ValueError(
            f"No valid closed trades were found in this {source} file after parsing. "
            "Check that it's a trade history export, not an open-positions or orders-only report."
        )

    return out


def parse_csv(path: str | Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    mapping = _map_columns(list(df.columns))
    return _finalize(df, mapping, source="CSV")


def parse_html(path: str | Path) -> pd.DataFrame:
    """A full HTML statement export (from MT5, cTrader, or similar) often
    contains multiple <table> elements (account summary, orders, deals,
    etc). We scan all of them and pick the one whose headers look most
    like a trade history table."""
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    soup = BeautifulSoup(content, "lxml")
    tables = soup.find_all("table")
    if not tables:
        raise ValueError("No <table> elements found in this HTML file.")

    best_df = None
    best_score = -1

    for table in tables:
        try:
            dfs = pd.read_html(io.StringIO(str(table)))
        except ValueError:
            continue
        for candidate in dfs:
            candidate.columns = [str(c) for c in candidate.columns]
            mapping = _map_columns(list(candidate.columns))
            score = sum(1 for f in REQUIRED_FIELDS if f in mapping)
            if score > best_score and score == len(REQUIRED_FIELDS):
                best_score = score
                best_df = (candidate, mapping)

    if best_df is None:
        raise ValueError(
            "Couldn't find a trade history table in this HTML file. "
            "Make sure it's the full statement/trade-history export, not a summary-only export."
        )

    candidate, mapping = best_df
    return _finalize(candidate, mapping, source="HTML")


def parse_trade_history(path: str | Path) -> pd.DataFrame:
    """Entry point: detects format from the file extension and parses it."""
    path = Path(path)
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return parse_csv(path)
    if suffix in (".html", ".htm"):
        return parse_html(path)
    raise ValueError(f"Unsupported file type '{suffix}'. Please provide a .csv or .html/.htm file.")
