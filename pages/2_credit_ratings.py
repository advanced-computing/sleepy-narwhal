"""
pages/2_credit_ratings.py
==========================
§2  Corporate bond market & credit ratings

Streamlit multi-page: this file runs directly (no render() wrapper).
Page title shown in sidebar: "Credit ratings"

Sections:
  A. What is a corporate bond — IG vs HY intro
  B. Credit rating system — 3-agency table (Fitch / S&P / Moody's)
  C. Current OAS by rating bucket + OAS history
  D. Average cumulative default rates by rating (interactive horizon)
  E. IG / HY issuance trend (full history)

Data sources:
  RATING_DF / DEFAULT_RATES_5Y          → data_utils (static)
  fred_daily_raw (section s2_ratings)   → FRED ICE BofA rating OAS
  static_avg_cumulative_default_rates   → S&P 2024 Default Study CSV
  static_corp_issuance                  → SIFMA Corporate Bonds CSV
"""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from data_utils import (
    DEFAULT_RATES_5Y,
    RATING_DF,
    get_avg_cumulative_default_rates,
    get_corp_issuance_annual,  # annual 2015-2025 → §2 long-term trend
    get_ig_hy_oas_history,
    get_rating_oas_history,
    get_rating_oas_latest,
)
from utils.perf import display_load_time

# ── Shared CSS ────────────────────────────────────────────────
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
  .src-badge { display: inline-block; font-size: 10px; font-weight: 600; padding: 2px 8px; border-radius: 99px; margin-right: 4px; }
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
IG_COLOR = "#4472C4"
HY_COLOR = "#E07B39"
PLOTLY_LAYOUT = dict(
    font_family="Inter, sans-serif",
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    margin=dict(l=40, r=20, t=30, b=40),
    xaxis=dict(showgrid=False, linecolor="#e0dfd8"),
    yaxis=dict(gridcolor="#f0efe8", linecolor="#e0dfd8"),
)


# ── Cached loaders ────────────────────────────────────────────
@st.cache_data(ttl=3600)
def _oas_latest():
    return get_rating_oas_latest()


@st.cache_data(ttl=3600)
def _oas_history():
    return get_rating_oas_history()


@st.cache_data(ttl=3600)
def _ig_hy_history():
    return get_ig_hy_oas_history()


@st.cache_data(ttl=86400)
def _avg_cum_dr():
    return get_avg_cumulative_default_rates()


@st.cache_data(ttl=86400)  # 24h — annual data, no need to refresh hourly
def _issuance():
    return get_corp_issuance_annual()


# ── Charts ────────────────────────────────────────────────────
def chart_oas_by_rating(df):
    ORDER = ["aaa_oas", "aa_oas", "a_oas", "bbb_oas", "bb_oas", "b_oas", "ccc_oas"]  # noqa: N806
    LABELS = {  # noqa: N806
        "aaa_oas": "AAA",
        "aa_oas": "AA",
        "a_oas": "A",
        "bbb_oas": "BBB",
        "bb_oas": "BB",
        "b_oas": "B",
        "ccc_oas": "CCC",
    }
    GRADE_COLORS = {  # noqa: N806
        "aaa_oas": "#1D9E75",
        "aa_oas": "#3B6D11",
        "a_oas": "#639922",
        "bbb_oas": "#BA7517",
        "bb_oas": "#E07B39",
        "b_oas": "#D85A30",
        "ccc_oas": "#A32D2D",
    }
    df_plot = df[df["series_key"].isin(ORDER)].copy()
    df_plot["order"] = df_plot["series_key"].map({k: i for i, k in enumerate(ORDER)})
    df_plot = df_plot.sort_values("order")
    fig = go.Figure(
        go.Bar(
            x=df_plot["value"],
            y=df_plot["series_key"].map(LABELS),
            orientation="h",
            marker_color=[GRADE_COLORS.get(k, "#999") for k in df_plot["series_key"]],
            text=[f"{v:.0f} bps" for v in df_plot["value"]],
            textposition="outside",
            hovertemplate="%{y}: %{x:.0f} bps<extra></extra>",
        )
    )
    fig.update_layout(
        **PLOTLY_LAYOUT,
        xaxis_title="OAS (basis points)",
        yaxis_title=None,
        height=300,
        showlegend=False,
    )
    return fig


def chart_oas_history(df):
    SERIES = {  # noqa: N806
        "bbb_oas": ("BBB", "#BA7517"),
        "bb_oas": ("BB", "#E07B39"),
        "b_oas": ("B", "#D85A30"),
        "ig_oas": ("IG overall", "#4472C4"),
        "hy_oas": ("HY overall", "#C0504D"),
    }
    fig = go.Figure()
    for col, (label, color) in SERIES.items():
        if col not in df.columns:
            continue
        fig.add_trace(
            go.Scatter(
                x=df["date"],
                y=df[col],
                name=label,
                line=dict(color=color, width=1.5),
                hovertemplate=f"{label}: %{{y:.0f}} bps<extra></extra>",
            )
        )
    fig.update_layout(
        **PLOTLY_LAYOUT,
        xaxis_title=None,
        yaxis_title="OAS (bps)",
        height=300,
        legend=dict(orientation="h", y=1.05, x=0, font_size=11),
    )
    return fig


def chart_default_rates(df, horizon="yr5"):
    if df.empty:
        ratings = list(DEFAULT_RATES_5Y.keys())
        rates = list(DEFAULT_RATES_5Y.values())
        grade = ["IG"] * 4 + ["HY"] * 3
    else:
        ratings = df["rating"].tolist()
        rates = df[horizon].tolist()
        grade = df["grade"].tolist()
    ig_shades = ["#1D9E75", "#3B6D11", "#639922", "#BA7517"]
    hy_shades = ["#E07B39", "#D85A30", "#A32D2D"]
    ig_i = hy_i = 0
    colors = []
    for g in grade:
        if g == "IG":
            colors.append(ig_shades[min(ig_i, len(ig_shades) - 1)])
            ig_i += 1
        else:
            colors.append(hy_shades[min(hy_i, len(hy_shades) - 1)])
            hy_i += 1
    fig = go.Figure(
        go.Bar(
            x=ratings,
            y=rates,
            marker_color=colors,
            text=[f"{r:.2f}%" for r in rates],
            textposition="outside",
            hovertemplate="%{x}: %{y:.2f}%<extra></extra>",
        )
    )
    fig.add_vline(
        x=3.5,
        line_dash="dash",
        line_color="#888780",
        annotation_text="IG / HY boundary",
        annotation_position="top right",
        annotation_font_size=10,
    )
    yr_label = horizon.replace("yr", "")
    fig.update_layout(
        **PLOTLY_LAYOUT,
        xaxis_title="Rating at origination",
        yaxis_title=f"{yr_label}Y cumulative default rate (%)",
        yaxis_range=[0, (max(rates) * 1.2) if rates else 70],
        height=300,
        showlegend=False,
    )
    return fig


def chart_ig_hy_issuance(df):
    """Stacked area: annual IG / HY gross issuance 2015-present."""
    if df.empty:
        return go.Figure()
    df = df.copy().sort_values("year")
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=df["year"].astype(str),
            y=df["hy_issuance_bn"],
            fill="tozeroy",
            name="HY",
            line=dict(color=HY_COLOR, width=1.5),
            fillcolor="rgba(224,123,57,0.2)",
            hovertemplate="%{x} HY: $%{y:,.1f}bn<extra></extra>",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df["year"].astype(str),
            y=df["ig_issuance_bn"],
            fill="tonexty",
            name="IG",
            line=dict(color=IG_COLOR, width=1.5),
            fillcolor="rgba(68,114,196,0.25)",
            hovertemplate="%{x} IG: $%{y:,.1f}bn<extra></extra>",
        )
    )
    fig.update_layout(
        **PLOTLY_LAYOUT,
        xaxis_title=None,
        yaxis_title="Gross issuance ($bn)",
        height=280,
        legend=dict(orientation="h", y=1.05, x=0, font_size=11),
    )
    return fig


def render_rating_table():
    df = RATING_DF[["fitch", "sp", "moodys", "description", "grade"]].copy()
    df = df.rename(
        columns={
            "fitch": "Fitch",
            "sp": "S&P",
            "moodys": "Moody's",
            "description": "Risk description",
            "grade": "Grade",
        }
    )

    def row_style(row):
        bg = "rgba(68,114,196,0.08)" if row["Grade"] == "IG" else "rgba(224,123,57,0.08)"
        return [f"background-color: {bg}"] * len(row)

    styled = df.style.apply(row_style, axis=1).set_properties(**{"font-size": "12px"})
    st.dataframe(styled, hide_index=True, use_container_width=True, height=560)


# ── Page ──────────────────────────────────────────────────────
_ctx = display_load_time()

with _ctx:
    st.markdown("## §2  Corporate bond market & credit ratings")

    # ── A. Intro ──────────────────────────────────────────────────
    st.markdown("""
    A **corporate bond** is a debt security issued by a corporation to raise capital.
    Unlike equities, bonds carry a fixed coupon and a contractual obligation to repay principal at maturity.
    The public corporate bond market — the focus of this dashboard — comprises bonds rated and traded in the
    US domestic market, as tracked by indices such as the ICE BofA US Corporate Index.
    """)

    col_ig, col_hy = st.columns(2)
    with col_ig:
        st.markdown("""
    **Investment Grade (IG) — BBB- / Baa3 and above**
    - Lower default risk · tighter spreads
    - Primary index: ICE BofA US Corporate Index (`BAMLC0A0CM`)
    - Outstanding: ~$7.2T (≈ 83% of US corp bonds)
    """)
    with col_hy:
        st.markdown("""
    **High Yield (HY) — BB+ / Ba1 and below**
    - Higher default risk · wider spreads · higher yield
    - Primary index: ICE BofA US HY Master II (`BAMLH0A0HYM2`)
    - Outstanding: ~$1.4T (≈ 17% of US corp bonds)
    """)

    st.markdown("---")

    # ── B. Rating system ──────────────────────────────────────────
    st.markdown("#### Credit rating system — Fitch / S&P / Moody's")
    st.markdown("Credit rating agencies assess the **probability of default** of a bond issuer. The **BBB- / Baa3** boundary is the critical dividing line between IG and HY.")

    tab_table, tab_explain = st.tabs(["Rating scale reference", "How ratings work"])
    with tab_table:
        col_tbl, col_note = st.columns([2, 1])
        with col_tbl:
            render_rating_table()
        with col_note:
            st.markdown("""
    **Key boundaries**

    | Boundary | Fitch/S&P | Moody's |
    |---|---|---|
    | Top IG | AAA | Aaa |
    | IG/HY line | BBB− | Baa3 |
    | Distressed | CCC | Caa |
    | Default | D | C |

    **Fallen angels** — downgraded IG→HY.
    Often cause forced selling.

    **Rising stars** — upgraded HY→IG.
    Trigger spread compression.
    """)
            st.markdown(
                '<p class="chart-caption">Source: Fitch, S&P, Moody\'s rating methodologies</p>',
                unsafe_allow_html=True,
            )
    with tab_explain:
        st.markdown("""
    Rating agencies evaluate a company's ability to service its debt. Key factors:

    - **Business risk** — industry dynamics, competitive position, regulation
    - **Financial risk** — leverage, interest coverage, cash flow, liquidity
    - **Management & governance** — track record, financial policy

    Ratings are not static — agencies issue upgrades, downgrades, outlook changes
    (positive/negative/stable), and watchlist notifications.

    > Rating agencies are paid by issuers, creating a potential conflict of interest.
    > Credit spreads often *lead* rating actions by several months.
    """)

    st.markdown("---")

    # ── C. OAS by rating ──────────────────────────────────────────
    st.markdown("#### Current OAS by rating — the market's price of credit risk")
    st.markdown("Option-Adjusted Spread (OAS) = yield premium over the Treasury curve, adjusted for embedded options. Higher OAS = higher default risk compensation demanded by the market.")

    oas_latest = _oas_latest()
    if not oas_latest.empty:
        col_bar, col_hist = st.columns([1, 1.4])
        with col_bar:
            st.markdown("**Current OAS (bps)**")
            st.plotly_chart(chart_oas_by_rating(oas_latest), use_container_width=True)
            latest_date = pd.Timestamp(oas_latest["date"].max()).strftime("%b %d, %Y")
            st.markdown(
                f'<p class="chart-caption"><span class="src-badge src-fred">FRED</span>'
                f"As of {latest_date}. ICE BofA rating-subset OAS indices. "
                f'<a href="https://fred.stlouisfed.org/release?rid=209" target="_blank">FRED ICE BofA Indices ↗</a></p>',
                unsafe_allow_html=True,
            )
        with col_hist:
            oas_hist = _oas_history()
            ig_hy = _ig_hy_history()
            merged = oas_hist.merge(ig_hy[["date", "ig_oas", "hy_oas"]], on="date", how="left") if not oas_hist.empty and not ig_hy.empty else oas_hist
            st.markdown("**OAS history — key buckets (2000–present)**")
            st.plotly_chart(chart_oas_history(merged), use_container_width=True)
            st.markdown(
                '<p class="chart-caption"><span class="src-badge src-fred">FRED</span>Series: BAMLC0A0CM, BAMLH0A0HYM2, BAMLC0A4CBBB, BAMLH0A1HYBB, BAMLH0A2HYB</p>',
                unsafe_allow_html=True,
            )
    else:
        st.info("OAS data not loaded. Run `data_load.py` first.")

    st.markdown("---")

    # ── D. Default rates ──────────────────────────────────────────
    st.markdown("#### Average cumulative default rates by rating")
    st.markdown("Historical average probability of default within N years by rating at origination. The sharp step at the **BBB/BB boundary** is the empirical basis for the IG/HY distinction.")

    horizon_map = {
        "1 year": "yr1",
        "2 years": "yr2",
        "3 years": "yr3",
        "5 years": "yr5",
        "7 years": "yr7",
        "10 years": "yr10",
    }
    horizon_label = st.radio("Time horizon", list(horizon_map.keys()), index=3, horizontal=True)
    cumdr_df = _avg_cum_dr()
    st.plotly_chart(chart_default_rates(cumdr_df, horizon=horizon_map[horizon_label]), use_container_width=True)
    st.markdown(
        '<p class="chart-caption"><span class="src-badge src-static">Static</span>'
        "S&P Global Ratings — 2024 Annual Global Corporate Default and Rating Transition Study, "
        "Table 7/8 (1981–2024 issuer-weighted averages). "
        '<a href="https://maalot.co.il/Publications/FTS20250331162126.pdf" target="_blank">PDF ↗</a> '
        "· Update each March.</p>",
        unsafe_allow_html=True,
    )

    st.markdown("---")

    # ── E. IG / HY issuance trend ─────────────────────────────────
    st.markdown("#### IG vs HY gross issuance — full history")
    iss_df = _issuance()
    if not iss_df.empty:
        st.plotly_chart(chart_ig_hy_issuance(iss_df), use_container_width=True)
        st.markdown(
            '<p class="chart-caption"><span class="src-badge src-sifma">SIFMA</span>'
            "Monthly gross issuance ($bn). HY collapses during credit stress (GFC, COVID). "
            '<a href="https://www.sifma.org/research/statistics/us-corporate-bonds-statistics" target="_blank">'
            "SIFMA US Corporate Bonds Statistics ↗</a></p>",
            unsafe_allow_html=True,
        )
    else:
        st.info("Add `data/corp_issuance.csv` and re-run `data_load.py`.")
