"""
Builds every Plotly figure used in the report, all sharing one visual
language (dark charcoal-navy background, gold accent, monospace-adjacent
number formatting) so the report reads as one designed artifact rather
than a pile of default chart styles.
"""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

# ---- design tokens (must match style.css) ----
BG = "#0d1017"
SURFACE = "#151a24"
GRID = "#232a38"
TEXT = "#e7e5df"
TEXT_MUTED = "#8b93a3"
GOLD = "#d4a24c"
GOLD_SOFT = "rgba(212,162,76,0.18)"
GREEN = "#3fb98a"
RED = "#e0605a"
FONT_FAMILY = "'IBM Plex Mono', 'Courier New', monospace"

BASE_LAYOUT = dict(
    paper_bgcolor=SURFACE,
    plot_bgcolor=SURFACE,
    font=dict(family=FONT_FAMILY, color=TEXT, size=12),
    margin=dict(l=50, r=20, t=20, b=40),
    hoverlabel=dict(bgcolor=BG, font_family=FONT_FAMILY, bordercolor=GOLD),
)


def _apply_grid(fig, x=True, y=True):
    fig.update_xaxes(showgrid=x, gridcolor=GRID, zeroline=False, linecolor=GRID)
    fig.update_yaxes(showgrid=y, gridcolor=GRID, zeroline=False, linecolor=GRID)
    return fig


def equity_curve_chart(equity_df: pd.DataFrame) -> str:
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=equity_df["open_time"],
        y=equity_df["cumulative_net"],
        mode="lines",
        line=dict(color=GOLD, width=2.5),
        fill="tozeroy",
        fillcolor=GOLD_SOFT,
        hovertemplate="%{x|%b %d, %Y}<br>Net: %{y:.2f}<extra></extra>",
    ))
    fig.update_layout(**BASE_LAYOUT, height=340, showlegend=False)
    _apply_grid(fig)
    fig.update_yaxes(title_text="Cumulative net P/L")
    return fig.to_html(full_html=False, include_plotlyjs=False, config={"displayModeBar": False})


def win_rate_bar_chart(breakdown_df: pd.DataFrame, label_col: str, height: int = 300) -> str:
    colors = [GREEN if wr >= 55 else (GOLD if wr >= 45 else RED) for wr in breakdown_df["win_rate"]]
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=breakdown_df[label_col].astype(str),
        y=breakdown_df["win_rate"],
        marker_color=colors,
        text=[f"{wr:.0f}%" for wr in breakdown_df["win_rate"]],
        textposition="outside",
        hovertemplate="%{x}<br>Win rate: %{y:.1f}%<extra></extra>",
    ))
    fig.update_layout(**BASE_LAYOUT, height=height, showlegend=False)
    _apply_grid(fig, x=False)
    fig.update_yaxes(title_text="Win rate %", range=[0, max(100, breakdown_df["win_rate"].max() + 15)])
    return fig.to_html(full_html=False, include_plotlyjs=False, config={"displayModeBar": False})


def net_profit_bar_chart(breakdown_df: pd.DataFrame, label_col: str, height: int = 300) -> str:
    colors = [GREEN if v >= 0 else RED for v in breakdown_df["net_profit"]]
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=breakdown_df[label_col].astype(str),
        y=breakdown_df["net_profit"],
        marker_color=colors,
        hovertemplate="%{x}<br>Net: %{y:.2f}<extra></extra>",
    ))
    fig.update_layout(**BASE_LAYOUT, height=height, showlegend=False)
    _apply_grid(fig, x=False)
    fig.update_yaxes(title_text="Net P/L")
    return fig.to_html(full_html=False, include_plotlyjs=False, config={"displayModeBar": False})


def monthly_net_chart(monthly_df: pd.DataFrame) -> str:
    colors = [GREEN if v >= 0 else RED for v in monthly_df["net_profit"]]
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=monthly_df["month"],
        y=monthly_df["net_profit"],
        marker_color=colors,
        hovertemplate="%{x}<br>Net: %{y:.2f}<extra></extra>",
    ))
    fig.update_layout(**BASE_LAYOUT, height=300, showlegend=False)
    _apply_grid(fig, x=False)
    fig.update_yaxes(title_text="Net P/L")
    return fig.to_html(full_html=False, include_plotlyjs=False, config={"displayModeBar": False})
