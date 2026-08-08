"""
Generates a realistic synthetic MT5 trade history — used to test and demo
the analyzer before running it against a real exported statement. Produces
both a CSV and an HTML export in MT5's typical shapes, covering multiple
symbols, sessions, setups, and a plausible win/loss distribution so the
analyzer's breakdowns have something meaningful to show.
"""

import random
from datetime import datetime, timedelta

SYMBOLS = ["NAS100", "XAUUSD", "EURUSD", "GBPUSD"]
SETUPS = ["FVG entry", "OB retest", "liquidity sweep", "MSS confirm", "breaker block"]

random.seed(42)


def random_session_time(base_date):
    """Bias trade open times toward real trading sessions (London/NY overlap
    gets the most volume, Asia the least, matching typical ICT/SMC activity)."""
    roll = random.random()
    if roll < 0.15:
        hour = random.randint(0, 6)  # Asia
    elif roll < 0.55:
        hour = random.randint(7, 11)  # London
    elif roll < 0.90:
        hour = random.randint(12, 16)  # NY / London-NY overlap
    else:
        hour = random.randint(17, 23)  # late NY
    minute = random.randint(0, 59)
    return base_date.replace(hour=hour, minute=minute, second=random.randint(0, 59))


def generate_trades(n=180, start_date=datetime(2025, 10, 1)):
    trades = []
    balance = 5000.0
    current_date = start_date

    for i in range(n):
        current_date += timedelta(hours=random.uniform(4, 30))
        open_time = random_session_time(current_date)
        symbol = random.choices(SYMBOLS, weights=[0.45, 0.30, 0.15, 0.10])[0]
        direction = random.choice(["buy", "sell"])
        setup = random.choice(SETUPS)

        # Give NAS100/XAUUSD (the "main" instruments) a slightly better edge,
        # and FVG/MSS setups a bit better win rate than the others, so the
        # breakdown charts actually show a meaningful difference.
        base_win_prob = 0.52
        if symbol in ("NAS100", "XAUUSD"):
            base_win_prob += 0.05
        if setup in ("FVG entry", "MSS confirm"):
            base_win_prob += 0.06

        is_win = random.random() < base_win_prob
        r_multiple = random.uniform(1.2, 3.2) if is_win else -random.uniform(0.6, 1.05)

        risk_amount = balance * random.uniform(0.005, 0.015)
        profit = round(risk_amount * r_multiple, 2)
        balance += profit

        duration_minutes = random.randint(8, 340)
        close_time = open_time + timedelta(minutes=duration_minutes)

        volume = round(random.choice([0.1, 0.2, 0.3, 0.5, 1.0]), 2)
        open_price = round(random.uniform(1.0, 20000.0), 2) if symbol != "EURUSD" and symbol != "GBPUSD" else round(random.uniform(1.05, 1.35), 5)
        price_move = abs(profit) / (volume * 100) if volume else 0
        close_price = open_price + price_move if (is_win == (direction == "buy")) else open_price - price_move

        trades.append({
            "open_time": open_time.strftime("%Y.%m.%d %H:%M:%S"),
            "close_time": close_time.strftime("%Y.%m.%d %H:%M:%S"),
            "symbol": symbol,
            "type": direction,
            "volume": volume,
            "open_price": open_price,
            "close_price": round(close_price, 5),
            "sl": round(open_price * (0.995 if direction == "buy" else 1.005), 5),
            "tp": round(open_price * (1.01 if direction == "buy" else 0.99), 5),
            "commission": -round(volume * 3.5, 2),
            "swap": round(random.uniform(-2, 0.5), 2),
            "profit": profit,
            "comment": setup,
            "balance": round(balance, 2),
        })

    return trades


def write_csv(trades, path):
    import csv
    fieldnames = ["open_time", "close_time", "symbol", "type", "volume", "open_price",
                  "close_price", "sl", "tp", "commission", "swap", "profit", "comment", "balance"]
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(trades)


def write_html(trades, path):
    """Mimics the shape of MT5's exported HTML statement closely enough for
    the analyzer's HTML parser to be tested against realistically: a plain
    <table> with a header row of MT5-style column names."""
    rows = "".join(
        f"<tr>"
        f"<td>{t['open_time']}</td><td>{t['symbol']}</td><td>{t['type']}</td>"
        f"<td>{t['volume']}</td><td>{t['open_price']}</td><td>{t['sl']}</td><td>{t['tp']}</td>"
        f"<td>{t['close_time']}</td><td>{t['close_price']}</td>"
        f"<td>{t['commission']}</td><td>{t['swap']}</td><td>{t['profit']}</td><td>{t['comment']}</td>"
        f"</tr>"
        for t in trades
    )
    html = f"""<html><body>
<table>
<tr>
<th>Time</th><th>Symbol</th><th>Type</th><th>Volume</th><th>Price</th><th>S / L</th><th>T / P</th>
<th>Time</th><th>Price</th><th>Commission</th><th>Swap</th><th>Profit</th><th>Comment</th>
</tr>
{rows}
</table>
</body></html>"""
    with open(path, "w") as f:
        f.write(html)


if __name__ == "__main__":
    trades = generate_trades(180)
    write_csv(trades, "sample_data/sample_trades.csv")
    write_html(trades, "sample_data/sample_trades.html")
    print(f"Generated {len(trades)} sample trades -> sample_data/sample_trades.csv and .html")
