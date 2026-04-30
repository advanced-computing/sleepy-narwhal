"""
Executive dashboard for the US corporate credit risk monitor.
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from data_utils import (
    compute_spread_percentile,
    compute_spread_zscore,
    generate_outlook,
    get_baa_aaa_yield_history,
    get_ig_hy_oas_history,
    get_moodys_defaults,
    regime_flag,
)
from utils.style import inject_css, render_sidebar

st.set_page_config(
    page_title="US Credit Risk Dashboard",
    page_icon="CR",
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_css()
render_sidebar()

IG_COLOR = "#4472C4"
HY_COLOR = "#E07B39"
PLOTLY_LAYOUT = dict(
    font_family="-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif",
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    margin=dict(l=10, r=10, t=10, b=18),
    xaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
    yaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
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


def chart_sparkline(df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    recent = df[df["date"] >= df["date"].max() - pd.DateOffset(months=6)].copy()
    fig.add_trace(go.Scatter(x=recent["date"], y=recent["ig_oas"], name="IG", line=dict(color=IG_COLOR, width=2), hovertemplate="%{x|%b %d}: %{y:.0f} bp<extra>IG</extra>"))
    fig.add_trace(go.Scatter(x=recent["date"], y=recent["hy_oas"], name="HY", line=dict(color=HY_COLOR, width=2), hovertemplate="%{x|%b %d}: %{y:.0f} bp<extra>HY</extra>"))
    fig.update_layout(**PLOTLY_LAYOUT, height=250)
    return fig


st.markdown("## Executive Dashboard")
st.markdown("Five-second read: is today business as usual, or does credit need attention?")

df = _spreads()
if df.empty:
    st.warning("No spread data available. Run `data_load.py` or check BigQuery credentials.")
    st.stop()

df["date"] = pd.to_datetime(df["date"])
df = df.sort_values("date")
latest = df.dropna(subset=["ig_oas", "hy_oas"]).iloc[-1]
prev = df.dropna(subset=["ig_oas", "hy_oas"]).iloc[-2]
ig_series = df.set_index("date")["ig_oas"].dropna()
hy_series = df.set_index("date")["hy_oas"].dropna()
ig_z = compute_spread_zscore(ig_series).iloc[-1]
hy_z = compute_spread_zscore(hy_series).iloc[-1]
ig_pct = compute_spread_percentile(ig_series)
hy_pct = compute_spread_percentile(hy_series)
regime_label, regime_color = regime_flag(hy_pct)

yld = _baa_aaa()
baa_aaa_trend = np.nan
if not yld.empty and "baa_aaa_spread" in yld.columns:
    yld["date"] = pd.to_datetime(yld["date"])
    baa_aaa_trend = _trend(yld.set_index("date")["baa_aaa_spread"], 63)

defaults = _defaults()
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
    baa_aaa_trend,
    default_trend,
)

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("IG OAS", f"{latest['ig_oas']:.0f} bp", f"{latest['ig_oas'] - prev['ig_oas']:+.0f} bp")
c2.metric("HY OAS", f"{latest['hy_oas']:.0f} bp", f"{latest['hy_oas'] - prev['hy_oas']:+.0f} bp")
c3.metric("HY-IG", f"{latest['hy_oas'] - latest['ig_oas']:.0f} bp", f"{(latest['hy_oas'] - latest['ig_oas']) - (prev['hy_oas'] - prev['ig_oas']):+.0f} bp")
c4.metric("HY z-score", f"{hy_z:+.2f}" if not np.isnan(hy_z) else "n/a")
c5.markdown(
    f'<div class="signal-card" style="border-left-color:{regime_color};padding:10px 14px;"><div class="signal-label" style="color:{regime_color};">REGIME</div><div class="signal-title">{regime_label}</div><div class="signal-body">{hy_pct:.0f}th percentile vs 10Y</div></div>',  # noqa: E501
    unsafe_allow_html=True,
)

left, right = st.columns([1.45, 1])
with left:
    st.markdown("#### IG / HY OAS, last 6 months")
    st.plotly_chart(chart_sparkline(df), use_container_width=True)
with right:
    tags_html = " ".join(f'<span class="tag">{tag}</span>' for tag in tags)
    st.markdown(
        f'<div class="signal-card" style="border-left-color:{border};min-height:214px;">'
        f'<div class="signal-label" style="color:{border};">STRATEGY SIGNAL</div>'
        f'<div class="signal-title">{headline}</div>'
        f'<div class="signal-body">{body}</div>'
        f'<div class="tag-row">{tags_html}</div>'
        f"</div>",
        unsafe_allow_html=True,
    )

asof = pd.Timestamp(latest["date"]).strftime("%Y-%m-%d 00:00 UTC")
st.markdown(
    f'<p class="chart-caption">Data as of {asof} | Next scheduled update 06:00 UTC | Not investment advice.</p>',
    unsafe_allow_html=True,
)
