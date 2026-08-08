"""
Renders the final self-contained HTML report: loads the Jinja2 template,
builds every chart, and fills in the stats computed by metrics.py.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from jinja2 import Environment, FileSystemLoader
import plotly.offline as pyo

from . import charts

TEMPLATE_DIR = Path(__file__).parent / "templates"


def render_report(stats: dict, output_path: str | Path) -> Path:
    env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)))
    template = env.get_template("report_template.html")
    css = (TEMPLATE_DIR / "style.css").read_text()

    equity_chart = charts.equity_curve_chart(stats["equity_curve"])
    session_winrate_chart = charts.win_rate_bar_chart(stats["by_session"], "session")
    session_profit_chart = charts.net_profit_bar_chart(stats["by_session"], "session")
    symbol_winrate_chart = charts.win_rate_bar_chart(stats["by_symbol"], "symbol")
    symbol_profit_chart = charts.net_profit_bar_chart(stats["by_symbol"], "symbol")
    dow_profit_chart = charts.net_profit_bar_chart(stats["by_day_of_week"], "day_of_week")
    monthly_chart = charts.monthly_net_chart(stats["by_month"])

    setup_table = stats["by_setup"].to_dict(orient="records") if not stats["by_setup"].empty else []

    trade_log_df = stats["trade_log"].copy()
    trade_log_df["open_time"] = trade_log_df["open_time"].dt.strftime("%Y-%m-%d %H:%M")
    # Most recent trades first in the log for easier scanning.
    trade_log = trade_log_df.sort_values("open_time", ascending=False).to_dict(orient="records")

    plotly_js = pyo.get_plotlyjs()

    html = template.render(
        css=css,
        plotly_js=plotly_js,
        overview=stats["overview"],
        drawdown=stats["drawdown"],
        streaks=stats["streaks"],
        equity_chart=equity_chart,
        session_winrate_chart=session_winrate_chart,
        session_profit_chart=session_profit_chart,
        symbol_winrate_chart=symbol_winrate_chart,
        symbol_profit_chart=symbol_profit_chart,
        dow_profit_chart=dow_profit_chart,
        monthly_chart=monthly_chart,
        setup_table=setup_table,
        trade_log=trade_log,
        symbol_range=", ".join(sorted(stats["by_symbol"]["symbol"].tolist())),
        generated_at=datetime.now().strftime("%Y-%m-%d %H:%M"),
    )

    output_path = Path(output_path)
    output_path.write_text(html, encoding="utf-8")
    return output_path
