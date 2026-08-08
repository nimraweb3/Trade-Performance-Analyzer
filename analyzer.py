"""
Trade Performance Analyzer — command-line entry point.

Usage:
    python analyzer.py --input path/to/statement.csv
    python analyzer.py --input path/to/statement.html --output my_report.html
"""

from __future__ import annotations

import argparse
import sys
import webbrowser
from pathlib import Path

from trade_analyzer.parser import parse_trade_history
from trade_analyzer.metrics import compute_all
from trade_analyzer.report import render_report


def main():
    parser = argparse.ArgumentParser(
        description="Analyze a trading history export (CSV or HTML, from MT4/MT5, cTrader, Binance, TradingView, or similar) and generate a visual performance report."
    )
    parser.add_argument("--input", "-i", required=True, help="Path to the trade history export (.csv or .html)")
    parser.add_argument("--output", "-o", default="output/report.html", help="Path to write the HTML report to")
    parser.add_argument("--no-open", action="store_true", help="Don't automatically open the report in a browser")
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: file not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    print(f"Reading trade history from {input_path}...")
    try:
        df = parse_trade_history(input_path)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Parsed {len(df)} closed trades. Computing statistics...")
    stats = compute_all(df)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    render_report(stats, output_path)

    print(f"\nReport generated: {output_path.resolve()}")
    print(f"  Total trades:  {stats['overview']['total_trades']}")
    print(f"  Win rate:      {stats['overview']['win_rate']}%")
    print(f"  Net profit:    {stats['overview']['net_profit']}")
    print(f"  Profit factor: {stats['overview']['profit_factor']}")

    if not args.no_open:
        webbrowser.open(f"file://{output_path.resolve()}")


if __name__ == "__main__":
    main()
