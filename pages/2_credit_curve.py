"""
Credit Curve page: rating buckets, relative value, and default compensation.
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from data_utils import RATING_DF, get_avg_cumulative_default_rates, get_rating_oas_history, get_rating_oas_latest
from utils.perf import display_load_time
from utils.style import inject_css, render_sidebar

inject_css()
render_sidebar()

RATING_ORDER = ["aaa_oas", "aa_oas", "a_oas", "bbb_oas", "bb_oas", "b_oas", "ccc_oas"]
RATING_LABELS = {"aaa_oas": "AAA", "aa_oas": "AA", "a_oas": "A", "bbb_oas": "BBB", "bb_oas": "BB", "b_oas": "B", "ccc_oas": "CCC"}
RATING_COLORS = {"aaa_oas": "#1D9E75", "aa_oas": "#3B6D11", "a_oas": "#6FAC3D", "bbb_oas": "#BA7517", "bb_oas": "#E07B39", "b_oas": "#D04E3A", "ccc_oas": "#A32D2D"}
PLOTLY_LAYOUT = dict(
    font_family="-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif",
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    margin=dict(l=44, r=18, t=18, b=36),
    legend=dict(orientation="h", y=1.05, x=0, font_size=11),
    xaxis=dict(showgrid=False, linecolor="#e2e8f0"),
    yaxis=dict(gridcolor="#f1f5f9", linecolor="#e2e8f0"),
)


@st.cache_data(ttl=3600)
def _latest():
    return get_rating_oas_latest()


@st.cache_data(ttl=3600)
def _history():
    return get_rating_oas_history()


@st.cache_data(ttl=86400)
def _cum_dr():
    return get_avg_cumulative_default_rates()


def _rating_frame(latest: pd.DataFrame, history: pd.DataFrame) -> pd.DataFrame:
    hist = history.copy()
    hist["date"] = pd.to_datetime(hist["date"])
    cutoff = hist["date"].max() - pd.DateOffset(years=5)
    avg = hist[hist["date"] >= cutoff][RATING_ORDER].mean().rename("five_year_avg")
    out = latest[latest["series_key"].isin(RATING_ORDER)].copy()
    out["rating"] = out["series_key"].map(RATING_LABELS)
    out["sort"] = out["series_key"].map({k: i for i, k in enumerate(RATING_ORDER)})
    out["five_year_avg"] = out["series_key"].map(avg)
    return out.sort_values("sort")


def chart_oas_by_rating(df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Bar(x=df["five_year_avg"], y=df["rating"], orientation="h", name="5Y avg", marker_color="rgba(100,116,139,0.25)", hovertemplate="%{y} 5Y avg: %{x:.0f} bp<extra></extra>"))
    fig.add_trace(go.Bar(x=df["value"], y=df["rating"], orientation="h", name="Current", marker_color=[RATING_COLORS[k] for k in df["series_key"]], text=[f"{v:.0f}" for v in df["value"]], textposition="outside", hovertemplate="%{y} current: %{x:.0f} bp<extra></extra>"))
    fig.update_layout(**PLOTLY_LAYOUT, barmode="overlay", height=330, xaxis_title="OAS (bp)", yaxis_title=None)
    fig.update_yaxes(autorange="reversed")
    return fig


def chart_risk_reward(oas_df: pd.DataFrame, dr_df: pd.DataFrame) -> go.Figure:
    points = []
    for key in RATING_ORDER:
        label = RATING_LABELS[key]
        oas_row = oas_df[oas_df["series_key"] == key]
        dr_row = dr_df[dr_df["rating"] == label]
        if not oas_row.empty and not dr_row.empty:
            points.append({"rating": label, "key": key, "oas": float(oas_row["value"].iloc[0]), "dr": float(dr_row["yr5"].iloc[0])})
    pts = pd.DataFrame(points)
    fig = go.Figure()
    if not pts.empty:
        x = pts["oas"].to_numpy()
        y = pts["dr"].to_numpy()
        slope, intercept = np.polyfit(x, y, 1)
        line_x = np.linspace(max(0, x.min() * 0.8), x.max() * 1.08, 80)
        fig.add_trace(go.Scatter(x=line_x, y=slope * line_x + intercept, mode="lines", name="Fair compensation line", line=dict(color="#64748b", dash="dash"), hoverinfo="skip"))
        fig.add_trace(go.Scatter(x=pts["oas"], y=pts["dr"], mode="markers+text", text=pts["rating"], textposition="top center", marker=dict(size=15, color=[RATING_COLORS[k] for k in pts["key"]], line=dict(color="white", width=1)), hovertemplate="%{text}<br>OAS: %{x:.0f} bp<br>5Y default rate: %{y:.2f}%<extra></extra>"))
        bbb = pts[pts["rating"] == "BBB"].iloc[0]
        bb = pts[pts["rating"] == "BB"].iloc[0]
        fig.add_shape(type="line", x0=bbb["oas"], y0=bbb["dr"], x1=bb["oas"], y1=bb["dr"], line=dict(color="#A32D2D", width=2, dash="dot"))
        fig.add_annotation(x=(bbb["oas"] + bb["oas"]) / 2, y=(bbb["dr"] + bb["dr"]) / 2, text="BBB-BB cliff", showarrow=True, arrowhead=2, font=dict(size=11, color="#A32D2D"))
    fig.update_layout(**PLOTLY_LAYOUT, height=360, xaxis_title="Current OAS (bp)", yaxis_title="5Y cumulative default rate (%)", showlegend=True)
    return fig


def chart_default_rates(df: pd.DataFrame, horizons: list[str]) -> go.Figure:
    fig = go.Figure()
    colors = {"yr1": "#94a3b8", "yr3": "#64748b", "yr5": "#E07B39", "yr10": "#A32D2D"}
    labels = {"yr1": "1Y", "yr3": "3Y", "yr5": "5Y", "yr10": "10Y"}
    for horizon in horizons:
        fig.add_trace(go.Bar(x=df["rating"], y=df[horizon], name=labels[horizon], marker_color=colors[horizon], text=[f"{v:.1f}%" for v in df[horizon]] if horizon == "yr5" else None, textposition="outside"))
    fig.add_vline(x=3.5, line_dash="dash", line_color="#64748b", annotation_text="IG / HY", annotation_position="top right")
    fig.update_layout(**PLOTLY_LAYOUT, barmode="group", height=310, xaxis_title=None, yaxis_title="Cumulative default rate (%)")
    return fig


def render_rating_table():
    df = RATING_DF[["fitch", "sp", "moodys", "description", "grade"]].rename(columns={"fitch": "Fitch", "sp": "S&P", "moodys": "Moody's", "description": "Risk description", "grade": "Grade"})
    st.dataframe(df, hide_index=True, use_container_width=True, height=360)


with display_load_time():
    st.markdown("## Credit Curve")
    st.markdown("Decision question: which rating bucket is being mispriced versus history and default risk?")

    latest = _latest()
    history = _history()
    dr = _cum_dr()
    if latest.empty or history.empty:
        st.warning("Rating OAS data is not available.")
        st.stop()

    rating_df = _rating_frame(latest, history)
    st.markdown("#### OAS by rating versus 5Y average")
    st.plotly_chart(chart_oas_by_rating(rating_df), use_container_width=True)

    col_l, col_r = st.columns([1.2, 1])
    with col_l:
        st.markdown("#### Risk-reward scatter")
        st.plotly_chart(chart_risk_reward(latest, dr), use_container_width=True)
    with col_r:
        st.markdown("#### 5Y cumulative default rate")
        st.plotly_chart(chart_default_rates(dr, ["yr5"]), use_container_width=True)

    with st.expander("Show 1Y / 3Y / 10Y default-rate horizons"):
        st.plotly_chart(chart_default_rates(dr, ["yr1", "yr3", "yr5", "yr10"]), use_container_width=True)

    with st.expander("Rating scale reference"):
        render_rating_table()

    latest_date = pd.Timestamp(latest["date"].max()).strftime("%Y-%m-%d")
    st.markdown(f'<p class="chart-caption"><span class="src-badge src-fred">FRED</span> ICE BofA rating OAS as of {latest_date}. <span class="src-badge src-static">S&P</span> 1981-2024 average cumulative default rates.</p>', unsafe_allow_html=True)
