# Trade Performance Analyzer

## Video Demo

> 🎥 https://youtu.be/LTSglfWG1-E
---

## Table of contents

- [What problem it solves](#what-problem-it-solves)
- [Features](#features)
- [Quickstart](#quickstart)
  - [1. Install dependencies](#1-install-dependencies)
  - [2. Generate a report from your own file](#2-generate-a-report-from-your-own-file)
  - [3. Try it on the sample data first](#3-try-it-on-the-sample-data-first)
- [Command line options](#command-line-options)
- [Supported platforms & file formats](#supported-platforms--file-formats)
- [What the report includes](#what-the-report-includes)
- [Project structure and what each file does](#project-structure-and-what-each-file-does)
- [How the pipeline works](#how-the-pipeline-works)
- [Design decisions](#design-decisions)

---

## What problem it solves

Most traders have a folder full of raw CSV or HTML exports, plus a bunch of hand-maintained spreadsheets that go stale within a week. To answer even basic questions — "What's my actual win rate after fees?", "Which sessions really work for me?", "Is setup A really worth the effort?" — you end up copy-pasting columns, reformatting timestamps, and second-guessing the math every time.

**Trade Performance Analyzer** takes that raw export and turns it into a polished, browser-ready report in a single command. Zero spreadsheets, zero manual formulas, zero internet required once the report is generated.

---

## Features

| Feature | What you get |
|---|---|
| ✅ Multi-platform parser | Reads MT4/MT5, cTrader, Binance, TradingView, and generic CSV/HTML exports |
| ✅ Core metrics | Win rate, profit factor, expectancy, max drawdown, longest win/loss streaks |
| ✅ Breakdowns | By session (Asia / London / NY), symbol, weekday, month, setup/strategy |
| ✅ Visuals | Equity curve, win-rate bars, monthly PnL charts |
| ✅ Standalone HTML | Report is a single file; charts embedded, works 100% offline |
| ✅ Terminal-style UI | Dark background, monospace numbers, gold accents — looks like a real trading dashboard |
| ✅ Friendly CLI | Plain-English errors instead of raw Python stack traces |
| ✅ Auto-open in browser | Report opens as soon as it's built (toggle off with `--no-open`) |

---

## Quickstart

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Generate a report from your own file

```bash
python analyzer.py --input your_export.csv
python analyzer.py --input your_export.html
python analyzer.py -i statement.csv -o output/my_report.html --no-open
```

### 3. Try it on the sample data first

```bash
python analyzer.py --input sample_data/sample_trades.csv
python analyzer.py --input sample_data/other_platform_sample.csv
python analyzer.py --input sample_data/sample_trades.html
```

The report is written to **`output/report.html`** by default and opens in your browser automatically.

---

## Command line options

| Flag | Short | Default | What it does |
|---|---|---|---|
| `--input` | `-i` | *(required)* | Trade history file (`.csv` or `.html`) |
| `--output` | `-o` | `output/report.html` | Where to write the final HTML report |
| `--no-open` |  | off | Don't auto-open the report in your browser after generation |

Example (Windows PowerShell):

```powershell
python analyzer.py `
  --input "C:\Trading\monthly_report.csv" `
  --output "C:\Trading\Reports\August.html" `
  --no-open
```

---

## Supported platforms & file formats

- **CSV or HTML** export
- Columns are auto-detected, so exact header names don't have to match
- Recognized aliases include:
  - `Profit` / `PnL` / `P&L` / `Realized PnL` / `Result`
  - `Type` / `Side` / `Direction` + `buy`/`sell`/`long`/`short`
  - `Symbol` / `Instrument` / `Pair` / `Ticker`
  - `Open Time` / `Entry Time` / `Date` / `DateTime`
  - `SL` / `TP` / `Commission` / `Swap` / `Comment`
- Known to work with **MT4 / MT5, cTrader, Binance, TradingView, and generic broker exports**

---

## What the report includes

At the top you get the **summary cards**:

- Total trades
- Net profit / loss
- Win rate
- Profit factor
- Expectancy per trade
- Average R:R (when SL/TP are present)
- Max drawdown
- Longest winning streak
- Longest losing streak

Then the breakdowns:

1. **Equity curve** — running PnL over time
2. **Trading session** — Asia / London / New York performance
3. **Symbol / instrument** — which markets are working
4. **Day of week** — see which days you actually trade well
5. **Month by month** — seasonal and account-growth view
6. **Setup / strategy** — grouped from the comment/notes field

---

## Project structure and what each file does

```text
Week-10/Final-Project/
├── analyzer.py                         # CLI entry point
├── requirements.txt                    # pandas, plotly, bs4, jinja2, lxml
├── sample_data/
│   ├── generate_sample.py              # MT5-style synthetic data
│   ├── generate_other_platform_sample.py
│   ├── sample_trades.csv
│   ├── sample_trades.html
│   └── other_platform_sample.csv
└── trade_analyzer/
    ├── __init__.py
    ├── parser.py                       # CSV + HTML normalizer (platform-agnostic)
    ├── metrics.py                      # Win rate / PF / drawdown / breakdowns
    ├── charts.py                       # Plotly charts with unified palette
    ├── report.py                       # Renders Jinja template to final HTML
    └── templates/
        ├── report_template.html
        └── style.css
```

The project is organized into a few clearly separated files, each handling one part of the process.

**`analyzer.py`** is the entry point  the file that actually gets run. It reads the command-line options, calls the parser, then the statistics calculator, then the report builder, in that order, and prints a short summary to the terminal once done. It also handles errors gracefully: if a file can't be read properly, it prints a plain, understandable message instead of crashing with a raw Python error.

**`trade_analyzer/parser.py`** is responsible for turning a messy CSV or HTML export into a clean, consistent table, regardless of which platform it came from. Different platforms label the same data differently — one might call a column "Profit," another might call the same value "Realized PnL" or "P&L." This file keeps a list of alternate names for each piece of data it needs (open time, symbol, direction, profit, and so on) and matches whichever version actually appears in the file. It also standardizes different ways of writing "buy" or "sell" (like "long," "b," or "buy") into one consistent value. For HTML exports specifically, MT5-style statements often contain several different tables on the same page  an account summary, an orders table, and a deals table — so the parser scans through all of them and identifies the one that actually looks like a trade history.

**`trade_analyzer/metrics.py`** takes the cleaned table and performs the actual calculations: win rate, profit factor, expectancy, drawdown, and the various breakdowns by session, symbol, day, month, and setup. This file has no knowledge of how anything will eventually be displayed  it simply returns numbers and small tables. Keeping it separate from the charting and report-building code was a deliberate choice, so the correctness of the calculations could be tested independently, without needing to look at a rendered web page every time a check was needed.

**`trade_analyzer/charts.py`** builds each individual chart — the equity curve, the win-rate bar charts, and the monthly performance chart  using the Plotly library. Every chart shares the same color palette and font choices, so the finished report looks like one cohesive, designed piece rather than a collection of default-looking charts stitched together.

**`trade_analyzer/report.py`** brings everything together: it takes the calculated numbers from `metrics.py` and the charts from `charts.py`, fills them into the HTML template, and saves the finished report file. The actual appearance of the report  the layout, the metric cards at the top, the tables, and the dark terminal-style color scheme  is controlled by `trade_analyzer/templates/report_template.html` and `style.css`.

Finally, **`sample_data/`** contains example trade files so the tool can be tested and demonstrated without needing a real trading account. Two separate sample generators are included on purpose: one that mimics MT5's typical export format, and a second (`generate_other_platform_sample.py`) that deliberately uses different column names and different wording for buy and sell (such as "long"/"short" instead of "buy"/"sell"), to prove that the parser genuinely works across different platforms rather than being hardcoded to a single one.

---

## How the pipeline works

```text
analyzer.py  --input report.csv
    │
    ▼
parser.py    ──► clean, normalized pandas DataFrame (same schema for any platform)
    │
    ▼
metrics.py   ──► overview + breakdowns (session / symbol / weekday / month / setup)
    │
    ▼
charts.py    ──► Plotly equity curve, win-rate bars, monthly chart
    │
    ▼
report.py    ──► Jinja2 template → final standalone HTML → output/report.html
```

---

## Design decisions

A few choices worth calling out:

1. **CLI over web app** — A trade report is one input → one file → one user. Adding login/auth/database would have added complexity without value, so the tool stays a single command.
2. **Loose column matching** — The first parser version only accepted MT5's exact headers. Real exports vary wildly, so it now matches many aliases for the same underlying field and normalizes trade directions like `long`/`short`/`b`/`s` into canonical `buy`/`sell`.
3. **Offline HTML** — The first version loaded Plotly from a CDN, which meant the report broke offline. The library code is now embedded into the HTML file itself, so a report can be opened or emailed without any internet.
4. **Separate metrics from visuals** — `metrics.py` returns pure numbers and tables, `charts.py` returns chart objects, `report.py` arranges them. That makes it easy to verify calculations without staring at a rendered page.
