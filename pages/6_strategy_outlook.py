"""
pages/6_Strategy_Outlook.py
=============================
Strategy outlook

Synthesises signals from §1–§5 into an actionable market view.

Sections:
  A. Market regime summary — automated signal dashboard
  B. Yield analysis — IG vs HY effective yield, Baa-Aaa spread
  C. Risk-reward map — OAS vs cumulative default rate by rating
  D. Automated outlook — rule-based narrative from current signals

Data sources:
  fred_daily_raw  — ig_oas, hy_oas, ig_yield, hy_yield, aaa_yield, baa_yield
  static_avg_cumulative_default_rates
  get_rating_oas_latest()
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from utils.style import inject_css, render_sidebar

from data_utils import (
    DEFAULT_RATES_5Y,
    compute_spread_percentile,
    compute_spread_zscore,
    get_avg_cumulative_default_rates,
    get_ig_hy_oas_history,
    get_rating_oas_latest,
    regime_flag,
)
from utils.perf import display_load_time

# ── CSS ───────────────────────────────────────────────────────
# CSS injected via utils/style.py
inject_css()
render_sidebar()

# ── Colors ────────────────────────────────────────────────────
IG_COLOR = "#4472C4"
HY_COLOR = "#E07B39"
RATING_COLORS = {
    "aaa_oas": "#1D9E75",
    "aa_oas": "#3B6D11",
    "a_oas": "#6FAC3D",
    "bbb_oas": "#BA7517",
    "bb_oas": "#E07B39",
    "b_oas": "#D04E3A",
    "ccc_oas": "#A32D2D",
}
RATING_LABELS = {
    "aaa_oas": "AAA",
    "aa_oas": "AA",
    "a_oas": "A",
    "bbb_oas": "BBB",
    "bb_oas": "BB",
    "b_oas": "B",
    "ccc_oas": "CCC",
}
PLOTLY_LAYOUT = dict(
    font_family="DM Sans, sans-serif",
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    margin=dict(l=36, r=12, t=20, b=30),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0, font_size=11, bgcolor="rgba(0,0,0,0)"),
    xaxis=dict(showgrid=False, linecolor="#e0dfd8"),
    yaxis=dict(gridcolor="#f0efe8", linecolor="#e0dfd8"),
)


# ── Cached loaders ────────────────────────────────────────────
@st.cache_data(ttl=3600)
def _ig_hy():
    return get_ig_hy_oas_history()


@st.cache_data(ttl=3600)
def _oas_latest():
    return get_rating_oas_latest()


@st.cache_data(ttl=86400)
def _cum_dr():
    return get_avg_cumulative_default_rates()


# ── Helper: yield query ───────────────────────────────────────
@st.cache_data(ttl=3600)
def _yield_history():
    """Baa and Aaa Moody's yield history from FRED."""
    from data_utils import _bq, _tbl

    q = f"""
        SELECT date, series_key, value
        FROM {_tbl("fred_daily_raw")}
        WHERE series_key IN ('baa_yield', 'aaa_yield')
          AND date >= '2000-01-01'
        ORDER BY date
    """
    long = _bq(q)
    if long.empty:
        return pd.DataFrame()
    return long.pivot_table(index="date", columns="series_key", values="value").reset_index()


# ── Charts ────────────────────────────────────────────────────


def chart_yield_history(df):
    """IG/HY effective yield + Baa-Aaa spread."""
    if df.empty:
        return go.Figure()
    fig = go.Figure()
    if "ig_yield" in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df["date"],
                y=df["ig_yield"],
                name="IG eff. yield",
                line=dict(color=IG_COLOR, width=1.5),
            )
        )
    if "hy_yield" in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df["date"],
                y=df["hy_yield"],
                name="HY eff. yield",
                line=dict(color=HY_COLOR, width=1.5),
            )
        )
    fig.update_layout(**PLOTLY_LAYOUT, yaxis_title="Yield (%)", height=250)
    return fig


def chart_baa_aaa_spread(yld_df):
    """Baa-Aaa yield spread as a credit stress indicator."""
    if yld_df.empty or "baa_yield" not in yld_df.columns:
        return go.Figure()
    df = yld_df.copy()
    df["date"] = pd.to_datetime(df["date"])
    df["spread"] = df["baa_yield"] - df["aaa_yield"]
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=df["date"],
            y=df["spread"],
            name="Baa – Aaa spread",
            line=dict(color="#6C5B7B", width=1.5),
            fill="tozeroy",
            fillcolor="rgba(108,91,123,0.1)",
        )
    )
    fig.update_layout(**PLOTLY_LAYOUT, yaxis_title="Spread (pp)", height=240)
    return fig


def chart_risk_reward(oas_df, cum_dr_df):
    """Scatter: current OAS (x) vs 5-yr cumulative default rate (y) by rating."""
    if oas_df.empty or cum_dr_df.empty:
        return go.Figure()

    fig = go.Figure()
    for key, label in RATING_LABELS.items():
        oas_row = oas_df[oas_df["series_key"] == key]
        if oas_row.empty:
            continue
        oas_val = oas_row["value"].iloc[0]

        # match rating to cumulative default rate
        dr_row = cum_dr_df[cum_dr_df["rating"] == label]
        if dr_row.empty:
            continue
        dr_5y = dr_row["yr5"].iloc[0]

        fig.add_trace(
            go.Scatter(
                x=[oas_val],
                y=[dr_5y],
                mode="markers+text",
                name=label,
                text=[label],
                textposition="top center",
                textfont=dict(size=11, color=RATING_COLORS.get(key, "#555")),
                marker=dict(
                    size=14,
                    color=RATING_COLORS.get(key, "#888"),
                    line=dict(width=1, color="white"),
                ),
                hovertemplate=f"{label}<br>OAS: %{{x:.0f}} bp<br>5yr DR: %{{y:.2f}}%<extra></extra>",
            )
        )

    fig.update_layout(
        **PLOTLY_LAYOUT,
        xaxis_title="Current OAS (bp)",
        yaxis_title="5-yr avg cumulative default rate (%)",
        height=280,
        showlegend=False,
    )
    return fig


# ── Signal generation ─────────────────────────────────────────


def generate_outlook(ig_z, hy_z, ig_pct, hy_pct, ig_oas, hy_oas, baa_aaa_spread=None):
    """
    Rule-based outlook generator. Returns (headline, body, border_color, tags).
    """
    tags = []
    ig_label, ig_color = regime_flag(ig_pct)
    hy_label, hy_color = regime_flag(hy_pct)
    tags.append(f"IG: {ig_label}")
    tags.append(f"HY: {hy_label}")
    tags.append(f"IG z: {ig_z:+.1f}")
    tags.append(f"HY z: {hy_z:+.1f}")
    tags.append(f"HY-IG: {hy_oas - ig_oas:.0f} bp")
    if baa_aaa_spread is not None:
        tags.append(f"Baa-Aaa: {baa_aaa_spread:.2f} pp")

    # determine overall regime
    stressed_threshold = 1.5
    rich_threshold = -1.5
    if hy_z > stressed_threshold and ig_z > stressed_threshold:
        headline = "Broad credit stress — caution warranted"
        body = (
            "Both IG and HY spreads are elevated relative to their 1-year averages, "
            "suggesting risk aversion across the credit spectrum. This environment "
            "historically favors defensive positioning: shorter duration, higher quality, "
            "and reduced HY exposure. Monitor for further deterioration or signs of stabilisation."
        )
        border = "#A32D2D"
    elif hy_z > stressed_threshold:
        headline = "HY under pressure — selective opportunities"
        body = (
            "HY spreads are widening while IG remains relatively stable, pointing to "
            "idiosyncratic or sector-specific stress rather than systemic risk. "
            "This may present selective opportunities in higher-quality HY (BB-rated) names, "
            "while avoiding the lowest-rated credits where default risk is elevated."
        )
        border = "#BA7517"
    elif hy_z < rich_threshold and ig_z < rich_threshold:
        headline = "Spreads tight across the board — limited upside"
        body = (
            "Both IG and HY spreads are compressed relative to history, leaving limited "
            "room for further tightening. Valuations suggest investors are being paid less "
            "for bearing credit risk. Consider reducing overweight positions and "
            "building liquidity buffers for potential spread widening."
        )
        border = "#185FA5"
    elif hy_pct > 50 and ig_pct < 40:
        headline = "IG-HY divergence — rotation opportunity"
        body = (
            "IG spreads are relatively tight while HY is wider than median. This "
            "divergence suggests the market is differentiating between credit quality tiers. "
            "Consider tactical rotation from IG into higher-quality HY (BB) for yield pick-up, "
            "while maintaining IG core for stability."
        )
        border = "#BA7517"
    else:
        headline = "Credit markets in normal range"
        body = (
            "IG and HY spreads are near their historical medians, with no strong "
            "directional signal. Market pricing implies moderate default expectations "
            "and reasonable compensation for credit risk. Maintain diversified exposure "
            "aligned with benchmark weights."
        )
        border = "#3B6D11"

    return headline, body, border, tags


# ── Page ──────────────────────────────────────────────────────
_ctx = display_load_time()

with _ctx:
    st.markdown("## Strategy outlook")
    st.markdown("Synthesising spread levels, z-scores, percentiles, and yield analysis into a rule-based market view for IG and HY corporate credit.")

    df = _ig_hy()

    if df.empty:
        st.warning("No data available. Ensure `fred_daily_raw` has been loaded.")
    else:
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date")

        ig_series = df.set_index("date")["ig_oas"].dropna()
        hy_series = df.set_index("date")["hy_oas"].dropna()

        ig_z_val = compute_spread_zscore(ig_series).iloc[-1]
        hy_z_val = compute_spread_zscore(hy_series).iloc[-1]
        ig_pct = compute_spread_percentile(ig_series)
        hy_pct = compute_spread_percentile(hy_series)
        latest = df.dropna(subset=["ig_oas", "hy_oas"]).iloc[-1]
        ig_oas = latest["ig_oas"]
        hy_oas = latest["hy_oas"]

        # Baa-Aaa spread
        yld_df = _yield_history()
        baa_aaa_val = None
        if not yld_df.empty and "baa_yield" in yld_df.columns and "aaa_yield" in yld_df.columns:
            yld_latest = yld_df.dropna().iloc[-1]
            baa_aaa_val = yld_latest["baa_yield"] - yld_latest["aaa_yield"]

        # ── A. Signal dashboard ───────────────────────────
        st.markdown("---")

        headline, body, border, signal_tags = generate_outlook(ig_z_val, hy_z_val, ig_pct, hy_pct, ig_oas, hy_oas, baa_aaa_val)

        tags_html = " ".join(f'<span class="tag">{t}</span>' for t in signal_tags)
        st.markdown(
            f'<div class="signal-card" style="border-left-color:{border};">'
            f'<div class="signal-label" style="color:{border};">STRATEGY SIGNAL</div>'
            f'<div class="signal-title">{headline}</div>'
            f'<div class="signal-body">{body}</div>'
            f'<div class="tag-row">{tags_html}</div>'
            f"</div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            f'<p style="font-size:11px;color:#888;">Signal auto-generated from current spread levels, '
            f"z-scores, and percentiles as of {latest['date'].strftime('%d %b %Y')}. "
            f"Not investment advice.</p>",
            unsafe_allow_html=True,
        )

        # ── B. KPI metrics ────────────────────────────────
        st.markdown("---")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("IG OAS", f"{ig_oas:.0f} bp")
        c2.metric("HY OAS", f"{hy_oas:.0f} bp")
        if "ig_yield" in df.columns and "hy_yield" in df.columns:
            ig_y = df["ig_yield"].dropna().iloc[-1]
            hy_y = df["hy_yield"].dropna().iloc[-1]
            c3.metric("IG yield", f"{ig_y:.2f}%")
            c4.metric("HY yield", f"{hy_y:.2f}%")
        elif baa_aaa_val is not None:
            c3.metric("Baa yield", f"{yld_latest['baa_yield']:.2f}%")
            c4.metric("Baa-Aaa spread", f"{baa_aaa_val:.2f} pp")

        # ── C. Yield history ──────────────────────────────
        st.markdown("---")
        st.markdown("#### IG & HY effective yield")
        st.plotly_chart(chart_yield_history(df), use_container_width=True)
        st.markdown(
            '<p class="chart-caption"><span class="src-badge src-fred">FRED</span>ICE BofA IG Effective Yield (BAMLC0A0CMEY) · HY (BAMLH0A0HYM2EY)</p>',
            unsafe_allow_html=True,
        )

        # ── D. Baa-Aaa spread ─────────────────────────────
        if not yld_df.empty:
            st.markdown("---")
            st.markdown("#### Baa – Aaa yield spread (credit stress indicator)")
            st.markdown(
                "The Baa-Aaa spread widens when the market prices higher default risk for lower-quality investment grade borrowers. Spikes historically coincide with recessions and credit events."
            )
            st.plotly_chart(chart_baa_aaa_spread(yld_df), use_container_width=True)
            st.markdown(
                '<p class="chart-caption"><span class="src-badge src-fred">FRED</span>Moody\'s Baa Corporate Bond Yield (BAA) minus Aaa (AAA)</p>',
                unsafe_allow_html=True,
            )

        # ── E. Risk-reward scatter ────────────────────────
        st.markdown("---")
        st.markdown("#### Risk-reward map — OAS vs 5-year default probability")
        st.markdown("Where does each rating bucket sit on the risk-reward spectrum? Higher OAS should compensate for higher default probability.")
        oas_latest = _oas_latest()
        cum_dr = _cum_dr()
        st.plotly_chart(chart_risk_reward(oas_latest, cum_dr), use_container_width=True)
        st.markdown(
            '<p class="chart-caption"><span class="src-badge src-fred">FRED</span>Current OAS · <span class="src-badge src-static">S&amp;P</span>1981–2024 avg cumulative default rate</p>',
            unsafe_allow_html=True,
        )
