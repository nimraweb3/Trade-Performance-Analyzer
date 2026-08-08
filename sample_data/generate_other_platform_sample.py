"""
Generates a second sample trade history in a deliberately different column
format — mimicking a cTrader/generic-broker-style export rather than MT5's
naming — to prove the parser's flexible column matching actually
generalizes across platforms, not just works on one specific export shape.
"""

import csv
import random
from datetime import datetime, timedelta

random.seed(7)

SYMBOLS = ["BTCUSD", "ETHUSD", "US30", "SPX500"]
STRATEGIES = ["breakout", "mean reversion", "trend follow", "range fade"]


def generate(n=90, start_date=datetime(2025, 11, 1)):
    rows = []
    current_date = start_date
    for i in range(n):
        current_date += timedelta(hours=random.uniform(6, 40))
        direction = random.choice(["long", "short"])  # note: not buy/sell
        is_win = random.random() < 0.53
        pnl = round(random.uniform(20, 400) if is_win else -random.uniform(15, 250), 2)
        close_time = current_date + timedelta(minutes=random.randint(10, 300))
        rows.append({
            "Date/Time": current_date.strftime("%Y-%m-%d %H:%M:%S"),
            "Close Date": close_time.strftime("%Y-%m-%d %H:%M:%S"),
            "Instrument": random.choice(SYMBOLS),
            "Trade Side": direction,  # long/short instead of buy/sell
            "Quantity": round(random.uniform(0.01, 2), 2),
            "Entry Price": round(random.uniform(100, 60000), 2),
            "Exit Price": round(random.uniform(100, 60000), 2),
            "Fee": -round(random.uniform(0.5, 5), 2),
            "Realized PnL": pnl,  # different profit column name
            "Strategy": random.choice(STRATEGIES),  # different comment column name
        })
    return rows


if __name__ == "__main__":
    rows = generate()
    with open("sample_data/other_platform_sample.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f"Generated {len(rows)} rows -> sample_data/other_platform_sample.csv")
