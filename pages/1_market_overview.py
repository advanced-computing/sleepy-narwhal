"""
pages/1_market_overview.py
===========================
§1  Market overview — size & composition

Streamlit multi-page: this file runs directly (no render() wrapper).
Page title shown in sidebar: "Market overview"

Charts:
  1. Global FI outstanding by region (stacked bar, 2010-2024)
  2. US FI market structure by asset class (donut)
  3. US corporate bond outstanding trend (area, quarterly)
  4. IG / HY gross issuance monthly (grouped bar, last 3 years)

Data sources:
  static_global_fi        → SIFMA Fact Book CSV        (data/global_fi_outstanding.csv)
  static_us_fi_structure  → SIFMA FI Statistics CSV    (data/us_fi_outstanding.csv)
  fred_quarterly_raw      → FRED NCBDBIQ027S            (auto-ingested daily)
  static_corp_issuance    → SIFMA Corporate Bonds CSV  (data/corp_issuance.csv)
"""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from data_utils import (
    get_corp_issuance_monthly,  # monthly: Mar 2025 onward → §1 bar chart
    get_corp_outstanding_quarterly,
    get_global_fi_outstanding,
    get_us_fi_structure,
    get_us_fi_structure_latest,
)
from utils.perf import display_load_time

# ── Shared CSS (duplicated here so page works standalone) ─────
st.markdown(
    """
<style>
  .block-container { padding-top: 1.5rem; padding-bottom: 2rem; }
  [data-testid="metric-container"] {
    background: #f8f8f6; border: 0.5px solid #e0dfd8;
    border-radius: 10px; padding: 14px 18px;
  }
  [data-testid="metric-container"] label { font-size: 12px !important; color: #73726c; }
  [data-testid="metric-container"] [data-testid="stMetricValue"] { font-size: 22px !important; }
  hr { border: none; border-top: 0.5px solid #e0dfd8; margin: 1.5rem 0; }
  .chart-caption { font-size: 11px; color: #888780; margin-top: 4px; }
  .src-badge { display: inline-block; font-size: 10px; font-weight: 600; padding: 2px 8px;
  border-radius: 99px; margin-right: 4px; }
  .src-fred   { background: #E6F1FB; color: #0C447C; }
  .src-sifma  { background: #EAF3DE; color: #27500A; }
  .src-static { background: #FAEEDA; color: #633806; }
  /* ── Sidebar ── */
  [data-testid="stSidebar"] { background: #1a1f2e !important; }
  [data-testid="stSidebar"] > div:first-child { padding-top: 0 !important; }
  [data-testid="stSidebarNav"]::before {
    content: "US Credit Risk Dashboard";
    display: block;
    padding: 22px 20px 16px;
    font-size: 15px;
    font-weight: 600;
    color: #e8eaf0;
    letter-spacing: -0.01em;
    border-bottom: 1px solid rgba(255,255,255,0.07);
    margin-bottom: 6px;
  }
  [data-testid="stSidebarNav"] { padding-top: 0 !important; }
  [data-testid="stSidebarNavLink"] {
    border-radius: 8px !important; margin: 2px 8px !important;
    padding: 10px 14px !important; color: #9ba3b8 !important;
    font-size: 13px !important; font-weight: 400 !important;
    transition: background 0.15s, color 0.15s !important;
  }
  [data-testid="stSidebarNavLink"]:hover {
    background: rgba(255,255,255,0.07) !important; color: #e8eaf0 !important;
  }
  [data-testid="stSidebarNavLink"][aria-current="page"] {
    background: rgba(99,130,235,0.18) !important;
    color: #a5b4fc !important; font-weight: 500 !important;
  }
  [data-testid="stSidebarNavLink"] span { color: inherit !important; }
  [data-testid="stSidebar"] section[data-testid="stSidebarUserContent"] {
    padding-top: 8px; border-top: 1px solid rgba(255,255,255,0.07);
  }
  [data-testid="stSidebar"] .stMarkdown p {
    color: #4a5278 !important; font-size: 11px !important; line-height: 1.6 !important;
  }
</style>
""",
    unsafe_allow_html=True,
)

# ── Colors ────────────────────────────────────────────────────
COLORS = {
    "us": "#E07B39",
    "eu": "#4472C4",
    "china": "#C0504D",
    "japan": "#9BBB59",
    "uk": "#8064A2",
    "australia": "#4BACC6",
    "canada": "#F79646",
    "hk": "#7F7F7F",
    "singapore": "#17375E",
    "switzerland": "#C0C0C0",
    "dm": "#BFBFBF",
    "em": "#D6D6D6",
}
REGION_LABELS = {
    "us": "US",
    "eu": "EU",
    "china": "China",
    "japan": "Japan",
    "uk": "UK",
    "australia": "Australia",
    "canada": "Canada",
    "hk": "Hong Kong",
    "singapore": "Singapore",
    "switzerland": "Switzerland",
    "dm": "DM Other",
    "em": "EM Other",
}
ASSET_COLORS = {
    "treasury": "#E07B39",
    "corporate": "#C0504D",
    "mbs": "#4472C4",
    "municipal": "#F0A500",
    "agency": "#9BBB59",
    "abs": "#8064A2",
    "money_market": "#B0B0B0",
}
PLOTLY_LAYOUT = dict(
    font_family="Inter, sans-serif",
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    margin=dict(l=40, r=20, t=30, b=40),
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="left",
        x=0,
        font_size=11,
        bgcolor="rgba(0,0,0,0)",
    ),
    xaxis=dict(showgrid=False, linecolor="#e0dfd8"),
    yaxis=dict(gridcolor="#f0efe8", linecolor="#e0dfd8"),
)


# ── Cached loaders ────────────────────────────────────────────
@st.cache_data(ttl=3600)
def _global_fi():
    return get_global_fi_outstanding()


@st.cache_data(ttl=3600)
def _us_structure():
    return get_us_fi_structure()


@st.cache_data(ttl=3600)
def _us_latest():
    return get_us_fi_structure_latest()


@st.cache_data(ttl=3600)
def _corp_outstanding():
    return get_corp_outstanding_quarterly()


@st.cache_data(ttl=3600)
def _corp_issuance():
    return get_corp_issuance_monthly()


# ── Charts ────────────────────────────────────────────────────
def chart_global_fi_stacked(df):
    region_cols = [
        "us",
        "eu",
        "china",
        "japan",
        "uk",
        "australia",
        "canada",
        "hk",
        "singapore",
        "switzerland",
        "dm",
        "em",
    ]
    fig = go.Figure()
    for col in reversed(region_cols):
        if col not in df.columns:
            continue
        fig.add_trace(
            go.Bar(
                x=df["year"].astype(str),
                y=df[col],
                name=REGION_LABELS.get(col, col),
                marker_color=COLORS.get(col, "#999"),
                hovertemplate="%{fullData.name}: $%{y:,.1f}bn<extra></extra>",
            )
        )
    fig.update_layout(
        **PLOTLY_LAYOUT,
        barmode="stack",
        xaxis_title=None,
        yaxis_title="USD bn",
        yaxis_tickformat=",",
        height=380,
    )
    return fig


def chart_us_fi_donut(latest):
    labels_map = {
        "treasury_bn": "Treasury",
        "corporate_bn": "Corporate",
        "mbs_bn": "MBS",
        "municipal_bn": "Municipal",
        "agency_bn": "Agency",
        "abs_bn": "ABS",
        "money_market_bn": "Money Market",
    }
    labels, values, colors, customdata = [], [], [], []
    for k, lbl in labels_map.items():
        v = latest.get(k)
        if not v or v <= 0:
            continue
        yr = latest.get(f"{k}_year", latest.get("data_year", ""))
        labels.append(lbl)
        values.append(v)
        colors.append(ASSET_COLORS.get(k.replace("_bn", ""), "#ccc"))
        customdata.append(yr)
    fig = go.Figure(
        go.Pie(
            labels=labels,
            values=values,
            marker_colors=colors,
            customdata=customdata,
            hole=0.55,
            textinfo="percent",
            textfont_size=11,
            hovertemplate="%{label}: $%{value:,.1f}bn (%{percent}) — %{customdata}<extra></extra>",
        )
    )
    layout = {
        **PLOTLY_LAYOUT,
        "height": 340,
        "showlegend": True,
        "legend": dict(orientation="v", x=1.02, y=0.5, font_size=11),
    }
    fig.update_layout(**layout)
    return fig


def chart_corp_outstanding_trend(df):
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=df["date"],
            y=df["value_T"],
            fill="tozeroy",
            line=dict(color="#C0504D", width=2),
            fillcolor="rgba(192,80,77,0.15)",
            hovertemplate="%{x|%Y-%m}: $%{y:.2f}T<extra></extra>",
        )
    )
    fig.update_layout(
        **PLOTLY_LAYOUT,
        xaxis_title=None,
        yaxis_title="USD Trillion",
        yaxis_tickformat=".1f",
        height=280,
        showlegend=False,
    )
    return fig


def chart_issuance_monthly(df):
    if df.empty:
        return go.Figure()
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])
    cutoff = df["date"].max() - pd.DateOffset(months=36)
    df = df[df["date"] >= cutoff]
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=df["date"],
            y=df["ig_issuance_bn"],
            name="IG",
            marker_color="#4472C4",
            hovertemplate="%{x|%b %Y} IG: $%{y:.0f}bn<extra></extra>",
        )
    )
    fig.add_trace(
        go.Bar(
            x=df["date"],
            y=df["hy_issuance_bn"],
            name="HY",
            marker_color="#E07B39",
            hovertemplate="%{x|%b %Y} HY: $%{y:.0f}bn<extra></extra>",
        )
    )
    fig.update_layout(**PLOTLY_LAYOUT, barmode="group", xaxis_title=None, yaxis_title="USD bn", height=280)
    return fig


# ── Page ──────────────────────────────────────────────────────
_ctx = display_load_time()

with _ctx:
    st.markdown("## §1  Market overview — size & composition")
    st.markdown("Establishing the macro context: how large is the global fixed income market, where does the US sit, and how is the US market structured.")

    latest = _us_latest()
    corp_df = _corp_outstanding()

    # KPI row
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Global FI outstanding", "$145.1T", "+2.4% YoY")
    total = latest.get("total_bn", 0)
    c2.metric("US FI outstanding", f"${total / 1000:.1f}T" if total else "—")
    corp_t = corp_df["value_T"].iloc[-1] if not corp_df.empty else 0
    c3.metric("US corp bonds", f"${corp_t:.1f}T" if corp_t else "—")
    c4.metric("Corp share of US FI", f"{latest.get('corporate_pct', 0):.1f}%")

    st.markdown(
        '<p class="chart-caption">Sources: SIFMA Capital Markets Fact Book 2025 · FRED Z.1 Flow of Funds</p>',
        unsafe_allow_html=True,
    )
    st.markdown("---")

    # Chart 1: Global FI
    st.markdown("#### Global fixed income outstanding by region")
    global_df = _global_fi()
    if not global_df.empty:
        st.plotly_chart(chart_global_fi_stacked(global_df), use_container_width=True)
        st.markdown(
            '<p class="chart-caption"><span class="src-badge src-static">Static</span>'
            "SIFMA Capital Markets Fact Book, Tab 1-09 · BIS debt securities statistics. "
            '<a href="https://www.sifma.org/research/statistics/fact-book" target="_blank">sifma.org/fact-book ↗</a>'
            " · Update annually.</p>",
            unsafe_allow_html=True,
        )
    else:
        st.info("Add `data/global_fi_outstanding.csv` and re-run `data_load.py`.")

    st.markdown("---")

    # Charts 2 + 3: US structure donut  |  Corp outstanding trend
    col_l, col_r = st.columns([1, 1.2])
    with col_l:
        st.markdown("#### US fixed income market structure")
        us_df = _us_structure()
        if not us_df.empty:
            st.plotly_chart(chart_us_fi_donut(latest), use_container_width=True)
            yr = int(us_df["year"].iloc[-1]) if "year" in us_df.columns else "latest"
            st.markdown(
                f'<p class="chart-caption"><span class="src-badge src-sifma">SIFMA</span>'
                f"As of {yr}. "
                f'<a href="https://www.sifma.org/research/statistics/us-fixed-income-securities-statistics" target="_blank">'
                f"SIFMA US Fixed Income Securities Statistics ↗</a></p>",
                unsafe_allow_html=True,
            )
        else:
            st.info("Add `data/us_fi_outstanding.csv` and re-run `data_load.py`.")

    with col_r:
        st.markdown("#### US corporate bond outstanding")
        if not corp_df.empty:
            st.plotly_chart(chart_corp_outstanding_trend(corp_df), use_container_width=True)
            st.markdown(
                '<p class="chart-caption"><span class="src-badge src-fred">FRED</span>'
                "Nonfinancial corporate debt securities outstanding. "
                "Series: <code>NCBDBIQ027S</code> · "
                '<a href="https://fred.stlouisfed.org/series/NCBDBIQ027S" target="_blank">fred.stlouisfed.org ↗</a></p>',
                unsafe_allow_html=True,
            )
        else:
            st.info("Run `data_load.py` to load FRED data.")
