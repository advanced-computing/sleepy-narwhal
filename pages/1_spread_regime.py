"""
Spread Regime page: where are IG/HY spreads versus history?
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from data_utils import compute_spread_percentile, compute_spread_zscore, get_ig_hy_oas_history, get_recession_periods, regime_flag
from utils.perf import display_load_time
from utils.style import inject_css, render_sidebar

inject_css()
render_sidebar()

IG_COLOR = "#4472C4"
HY_COLOR = "#E07B39"
PLOTLY_LAYOUT = dict(
    font_family="-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif",
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    margin=dict(l=42, r=16, t=18, b=34),
    legend=dict(orientation="h", y=1.05, x=0, font_size=11),
    xaxis=dict(showgrid=False, linecolor="#e2e8f0"),
    yaxis=dict(gridcolor="#f1f5f9", linecolor="#e2e8f0"),
)


@st.cache_data(ttl=3600)
def _spreads():
    return get_ig_hy_oas_history()


def _add_recessions(fig: go.Figure, recessions: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp) -> None:
    for row in recessions.itertuples(index=False):
        x0 = max(row.start, start)
        x1 = min(row.end, end)
        if x0 <= x1:
            fig.add_vrect(x0=x0, x1=x1, fillcolor="#94a3b8", opacity=0.16, line_width=0, layer="below")


def _rolling_percentile(series: pd.Series, window: int = 2520) -> pd.Series:
    return series.rolling(window, min_periods=252).apply(lambda x: float((x < x[-1]).mean() * 100), raw=True)


def _range_filter(df: pd.DataFrame, label: str) -> pd.DataFrame:
    if label == "Max":
        return df
    years = int(label.replace("Y", ""))
    return df[df["date"] >= df["date"].max() - pd.DateOffset(years=years)]


def chart_oas_history(df: pd.DataFrame, full_df: pd.DataFrame, recessions: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    x_start = pd.Timestamp(df["date"].min())
    x_end = pd.Timestamp(df["date"].max())
    _add_recessions(fig, recessions, x_start, x_end)
    ten_year = full_df[full_df["date"] >= full_df["date"].max() - pd.DateOffset(years=10)]
    ig_med = ten_year["ig_oas"].median()
    hy_med = ten_year["hy_oas"].median()
    fig.add_trace(go.Scatter(x=df["date"], y=df["ig_oas"], name="IG OAS", line=dict(color=IG_COLOR, width=1.8), customdata=np.stack([df["ig_z"], df["ig_pct"]], axis=-1), hovertemplate="%{x|%Y-%m-%d}<br>IG: %{y:.0f} bp<br>z: %{customdata[0]:+.2f}<br>%ile: %{customdata[1]:.0f}<extra></extra>"))
    fig.add_trace(go.Scatter(x=df["date"], y=df["hy_oas"], name="HY OAS", line=dict(color=HY_COLOR, width=1.8), customdata=np.stack([df["hy_z"], df["hy_pct"]], axis=-1), hovertemplate="%{x|%Y-%m-%d}<br>HY: %{y:.0f} bp<br>z: %{customdata[0]:+.2f}<br>%ile: %{customdata[1]:.0f}<extra></extra>"))
    fig.add_hline(y=ig_med, line_dash="dash", line_color=IG_COLOR, opacity=0.55, annotation_text=f"IG 10Y median {ig_med:.0f}", annotation_position="bottom right")
    fig.add_hline(y=hy_med, line_dash="dash", line_color=HY_COLOR, opacity=0.55, annotation_text=f"HY 10Y median {hy_med:.0f}", annotation_position="top right")
    fig.update_layout(**PLOTLY_LAYOUT, height=390, yaxis_title="OAS (bp)")
    fig.update_xaxes(range=[x_start, x_end])
    return fig


def chart_zscore(df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    fig.add_hrect(y0=2, y1=4, fillcolor="rgba(163,45,45,0.08)", line_width=0)
    fig.add_hrect(y0=-4, y1=-2, fillcolor="rgba(24,95,165,0.08)", line_width=0)
    fig.add_hline(y=0, line_dash="dot", line_color="#94a3b8", line_width=1)
    fig.add_hline(y=2, line_dash="dot", line_color="#A32D2D", annotation_text="stressed", annotation_position="top right")
    fig.add_hline(y=-2, line_dash="dot", line_color="#185FA5", annotation_text="rich", annotation_position="bottom right")
    fig.add_trace(go.Scatter(x=df["date"], y=df["ig_z"], name="IG z-score", line=dict(color=IG_COLOR, width=1.5), hovertemplate="%{x|%Y-%m-%d}<br>IG z: %{y:+.2f}<extra></extra>"))
    fig.add_trace(go.Scatter(x=df["date"], y=df["hy_z"], name="HY z-score", line=dict(color=HY_COLOR, width=1.5), hovertemplate="%{x|%Y-%m-%d}<br>HY z: %{y:+.2f}<extra></extra>"))
    fig.update_layout(**PLOTLY_LAYOUT, height=260, yaxis_title="252d z-score")
    fig.update_xaxes(range=[pd.Timestamp(df["date"].min()), pd.Timestamp(df["date"].max())])
    return fig


with display_load_time():
    st.markdown("## Spread Regime")
    st.markdown("Decision question: are current spreads cheap, rich, or signalling stress?")

    df = _spreads()
    if df.empty:
        st.warning("No spread data available.")
        st.stop()

    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date")
    ig = df.set_index("date")["ig_oas"].dropna()
    hy = df.set_index("date")["hy_oas"].dropna()
    df["ig_z"] = compute_spread_zscore(ig).reindex(df["date"]).to_numpy()
    df["hy_z"] = compute_spread_zscore(hy).reindex(df["date"]).to_numpy()
    df["ig_pct"] = _rolling_percentile(ig).reindex(df["date"]).to_numpy()
    df["hy_pct"] = _rolling_percentile(hy).reindex(df["date"]).to_numpy()

    _, control = st.columns([3, 2])
    with control:
        horizon = st.segmented_control("Range", ["1Y", "3Y", "5Y", "10Y", "Max"], default="5Y", label_visibility="collapsed")
    shown = _range_filter(df, horizon)

    st.markdown("#### OAS history with recession bars")
    st.plotly_chart(chart_oas_history(shown, df, get_recession_periods()), use_container_width=True)

    left, right = st.columns([3, 1])
    with left:
        st.markdown("#### Z-score panel")
        st.plotly_chart(chart_zscore(shown), use_container_width=True)
    with right:
        latest = df.dropna(subset=["ig_oas", "hy_oas"]).iloc[-1]
        ig_pct = compute_spread_percentile(ig)
        hy_pct = compute_spread_percentile(hy)
        ig_label, ig_color = regime_flag(ig_pct)
        hy_label, hy_color = regime_flag(hy_pct)
        signal = "IG-HY divergence" if hy_pct > 50 and ig_pct < 40 else "Broad stress" if hy_pct >= 75 and ig_pct >= 75 else "Normal range"
        st.markdown(
            f'<div class="signal-card" style="border-left-color:{hy_color};">'
            f'<div class="signal-label" style="color:{hy_color};">REGIME SUMMARY</div>'
            f'<div class="signal-body"><b>IG regime:</b> {ig_label} ({ig_pct:.0f}th %ile)<br>'
            f'<b>HY regime:</b> {hy_label} ({hy_pct:.0f}th %ile)<br>'
            f'<b>Signal:</b> {signal}<br><br>'
            f'<span class="chart-caption">As of {pd.Timestamp(latest["date"]).strftime("%Y-%m-%d")}</span></div></div>',
            unsafe_allow_html=True,
        )

    st.markdown('<p class="chart-caption"><span class="src-badge src-fred">FRED</span> ICE BofA IG/HY OAS. Grey bars: NBER recessions.</p>', unsafe_allow_html=True)
