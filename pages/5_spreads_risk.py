"""
Spread vs Macro page: are wider spreads noise or fundamental deterioration?
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from data_utils import (
    compute_spread_percentile,
    compute_spread_zscore,
    generate_outlook,
    get_baa_aaa_yield_history,
    get_ig_hy_oas_history,
    get_moodys_defaults,
    get_recession_periods,
)
from utils.perf import display_load_time
from utils.style import inject_css, render_sidebar

inject_css()
render_sidebar()

HY_COLOR = "#E07B39"
PLOTLY_LAYOUT = dict(
    font_family="-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif",
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    margin=dict(l=44, r=18, t=18, b=36),
    legend=dict(orientation="h", y=1.05, x=0, font_size=11),
)


@st.cache_data(ttl=3600)
def _spreads():
    return get_ig_hy_oas_history()


@st.cache_data(ttl=3600)
def _baa_aaa():
    return get_baa_aaa_yield_history()


@st.cache_data(ttl=86400)
def _defaults():
    return get_moodys_defaults()


def _trend(series: pd.Series, periods: int) -> float:
    clean = series.dropna()
    if len(clean) <= periods:
        return np.nan
    return float(clean.iloc[-1] - clean.iloc[-periods])


def _add_recessions(fig: go.Figure, recessions: pd.DataFrame) -> None:
    for row in recessions.itertuples(index=False):
        fig.add_vrect(x0=row.start, x1=row.end, fillcolor="#94a3b8", opacity=0.16, line_width=0, layer="below")


def chart_hy_oas_vs_default(spread_df: pd.DataFrame, default_df: pd.DataFrame) -> go.Figure:
    if spread_df.empty or default_df.empty:
        return go.Figure()

    sdf = spread_df[["date", "hy_oas"]].dropna().copy()
    sdf["year"] = pd.to_datetime(sdf["date"]).dt.year
    annual = sdf.groupby("year", as_index=False)["hy_oas"].mean()
    merged = annual.merge(default_df[["year", "sg_default_rate"]], on="year", how="inner")

    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.08, row_heights=[0.55, 0.45])
    fig.add_trace(
        go.Bar(
            x=merged["year"],
            y=merged["hy_oas"],
            name="HY OAS avg",
            marker_color="rgba(224,123,57,0.45)",
            hovertemplate="%{x}<br>HY OAS: %{y:.0f} bp<extra></extra>",
        ),
        row=1,
        col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=merged["year"],
            y=merged["sg_default_rate"],
            name="SG default rate",
            mode="lines+markers",
            line=dict(color="#A32D2D", width=2),
            hovertemplate="%{x}<br>SG default rate: %{y:.1f}%<extra></extra>",
        ),
        row=2,
        col=1,
    )
    fig.update_layout(
        **PLOTLY_LAYOUT,
        height=430,
        xaxis2=dict(showgrid=False, linecolor="#e2e8f0"),
        yaxis=dict(title="OAS (bp)", gridcolor="#f1f5f9"),
        yaxis2=dict(title="Default rate (%)", gridcolor="#f1f5f9"),
    )
    return fig


def chart_baa_aaa(df: pd.DataFrame, recessions: pd.DataFrame) -> go.Figure:
    if df.empty or "baa_aaa_spread" not in df.columns:
        return go.Figure()

    fig = go.Figure()
    _add_recessions(fig, recessions)
    fig.add_trace(
        go.Scatter(
            x=df["date"],
            y=df["baa_aaa_spread"],
            name="Baa-Aaa spread",
            line=dict(color="#6C5B7B", width=1.6),
            fill="tozeroy",
            fillcolor="rgba(108,91,123,0.14)",
            hovertemplate="%{x|%Y-%m-%d}<br>Baa-Aaa: %{y:.2f} pp<extra></extra>",
        )
    )
    fig.update_layout(
        **PLOTLY_LAYOUT,
        height=320,
        xaxis=dict(showgrid=False, linecolor="#e2e8f0"),
        yaxis=dict(title="Spread (pp)", gridcolor="#f1f5f9", linecolor="#e2e8f0"),
    )
    return fig


with display_load_time():
    st.markdown("## Spread vs Macro")
    st.markdown("Decision question: is spread widening just market noise, or are fundamentals deteriorating?")

    spreads = _spreads()
    defaults = _defaults()
    baa_aaa = _baa_aaa()

    if spreads.empty:
        st.warning("No spread data available.")
        st.stop()

    spreads["date"] = pd.to_datetime(spreads["date"])
    spreads = spreads.sort_values("date")
    latest = spreads.dropna(subset=["ig_oas", "hy_oas"]).iloc[-1]
    ig = spreads.set_index("date")["ig_oas"].dropna()
    hy = spreads.set_index("date")["hy_oas"].dropna()
    ig_z = compute_spread_zscore(ig).iloc[-1]
    hy_z = compute_spread_zscore(hy).iloc[-1]
    ig_pct = compute_spread_percentile(ig)
    hy_pct = compute_spread_percentile(hy)

    baa_trend = np.nan
    if not baa_aaa.empty and "baa_aaa_spread" in baa_aaa.columns:
        baa_aaa["date"] = pd.to_datetime(baa_aaa["date"])
        baa_trend = _trend(baa_aaa.set_index("date")["baa_aaa_spread"], 63)

    default_trend = np.nan
    if not defaults.empty and len(defaults.dropna(subset=["sg_default_rate"])) > 1:
        default_trend = float(defaults["sg_default_rate"].dropna().iloc[-1] - defaults["sg_default_rate"].dropna().iloc[-2])

    headline, body, border, tags = generate_outlook(
        ig_z,
        hy_z,
        ig_pct,
        hy_pct,
        float(latest["ig_oas"]),
        float(latest["hy_oas"]),
        baa_trend,
        default_trend,
    )
    tags_html = " ".join(f'<span class="tag">{tag}</span>' for tag in tags)
    st.markdown(
        f'<div class="signal-card" style="border-left-color:{border};">'
        f'<div class="signal-label" style="color:{border};">STRATEGY SIGNAL</div>'
        f'<div class="signal-title">{headline}</div>'
        f'<div class="signal-body">{body}</div>'
        f'<div class="tag-row">{tags_html}</div></div>',
        unsafe_allow_html=True,
    )

    st.markdown("#### HY OAS vs speculative-grade default rate")
    st.plotly_chart(chart_hy_oas_vs_default(spreads, defaults), use_container_width=True)

    if not baa_aaa.empty and "baa_aaa_spread" in baa_aaa.columns:
        st.markdown("#### Baa-Aaa spread")
        st.plotly_chart(chart_baa_aaa(baa_aaa, get_recession_periods()), use_container_width=True)

    st.markdown(
        '<p class="chart-caption"><span class="src-badge src-fred">FRED</span> HY OAS and Moody corporate yields. '
        '<span class="src-badge src-static">S&amp;P</span> Speculative-grade default rates. Grey bars: NBER recessions.</p>',
        unsafe_allow_html=True,
    )
