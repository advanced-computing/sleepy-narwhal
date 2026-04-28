"""
data_utils.py
=============
All data-fetching and calculation functions for the dashboard.
Called by Streamlit pages — never contains UI code.

BigQuery read pattern:
  Every public function returns a pd.DataFrame.
  Use @st.cache_data(ttl=3600) at the call site in pages.
"""

import numpy as np
import pandas as pd
import streamlit as st
from google.cloud import bigquery
from google.oauth2 import service_account

# ==========================================
# Config
# ==========================================
PROJECT_ID = "sipa-adv-c-sleepy-narwhal"
DATASET_ID = "credit_risk_data"


def _bq_client() -> bigquery.Client:
    """
    Returns an authenticated BigQuery client.

    On Streamlit Cloud: reads service account JSON from st.secrets["gcp_service_account"].
    Locally: falls back to Application Default Credentials (gcloud auth).
    """
    if "gcp_service_account" in st.secrets:
        credentials = service_account.Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=["https://www.googleapis.com/auth/cloud-platform"],
        )
        return bigquery.Client(project=PROJECT_ID, credentials=credentials)
    # local dev — uses gcloud auth application-default login
    return bigquery.Client(project=PROJECT_ID)


def _bq(query: str) -> pd.DataFrame:
    return _bq_client().query(query).to_dataframe(create_bqstorage_client=False)


def _tbl(name: str) -> str:
    return f"`{PROJECT_ID}.{DATASET_ID}.{name}`"


# ==========================================
# §1 — Market overview helpers
# ==========================================


def get_global_fi_outstanding() -> pd.DataFrame:
    """
    Global FI outstanding by region 2010-2024.
    Returns: wide DataFrame, columns = [year, us, eu, china, japan, uk, ...]  units: $bn
    Source: static_global_fi (from SIFMA Fact Book CSV)
    """
    q = f"""
        SELECT year, us, eu, china, japan, uk, australia,
               canada, hk, singapore, switzerland, dm, em, total
        FROM {_tbl("static_global_fi")}
        ORDER BY year
    """
    return _bq(q)


def get_us_fi_structure() -> pd.DataFrame:
    """
    US fixed income outstanding by asset class, annual.
    Returns: [year, treasury_bn, corporate_bn, mbs_bn, municipal_bn, agency_bn, abs_bn, money_market_bn]
    Source: static_us_fi_structure (from SIFMA quarterly Excel)
    """
    q = f"""
        SELECT year, treasury_bn, corporate_bn, mbs_bn,
               municipal_bn, agency_bn, abs_bn, money_market_bn
        FROM {_tbl("static_us_fi_structure")}
        ORDER BY year
    """
    return _bq(q)


def get_us_fi_structure_latest() -> dict:
    """
    Latest available value per asset class, with total and share computed.

    MBS and ABS are NaN from 2022 onward in the SIFMA source — we take the
    last non-NaN value independently for each column so the donut chart and
    KPI cards still render correctly.

    Returns dict with keys:
      treasury_bn, corporate_bn, mbs_bn, municipal_bn, agency_bn, abs_bn,
      money_market_bn, total_bn, <each>_pct, data_year
    """
    df = get_us_fi_structure()
    if df.empty:
        return {}

    COLS = [  # noqa: N806
        "treasury_bn",
        "corporate_bn",
        "mbs_bn",
        "municipal_bn",
        "agency_bn",
        "abs_bn",
        "money_market_bn",
    ]

    # For each column take the last non-NaN row independently
    result: dict = {}
    for col in COLS:
        col_series = df[["year", col]].dropna(subset=[col])
        if not col_series.empty:
            result[col] = col_series[col].iloc[-1]
            result[f"{col}_year"] = int(col_series["year"].iloc[-1])
        else:
            result[col] = 0.0
            result[f"{col}_year"] = None

    # Total uses the most recent complete row where all 7 cols are available
    total = sum(result.get(c, 0) or 0 for c in COLS)
    result["total_bn"] = total
    result["data_year"] = int(df["year"].iloc[-1])  # latest year in file

    for c in COLS:
        v = result.get(c, 0) or 0
        result[f"{c.replace('_bn', '')}_pct"] = round(v / total * 100, 2) if total else 0

    return result


def get_corp_outstanding_quarterly() -> pd.DataFrame:
    """
    Corporate bond outstanding from FRED Z.1 (quarterly, $mn → converted to $T).
    Returns: [date, value_T]   (nonfinancial corp debt securities)
    Source: fred_quarterly_raw, series_key = 'corp_outstanding'
    """
    q = f"""
        SELECT date, value / 1e6 AS value_T
        FROM {_tbl("fred_quarterly_raw")}
        WHERE series_key = 'corp_outstanding'
        ORDER BY date
    """
    return _bq(q)


def get_corp_issuance_monthly() -> pd.DataFrame:
    """
    IG and HY gross issuance, monthly ($bn).
    Returns: [date, ig_issuance_bn, hy_issuance_bn, total_bn]
    Source: static_corp_issuance_monthly  (data/corp_issuance_monthly.csv)
    Coverage: Mar 2025 onward. Used in §1 monthly bar chart.
    """
    # total_bn computed in SQL — avoids a Python round-trip
    q = f"""
        SELECT date, ig_issuance_bn, hy_issuance_bn,
               ig_issuance_bn + hy_issuance_bn AS total_bn
        FROM {_tbl("static_corp_issuance_monthly")}
        ORDER BY date
    """
    return _bq(q)


def get_corp_issuance_annual() -> pd.DataFrame:
    """
    IG and HY gross issuance, annual ($bn).
    Returns: [year, ig_issuance_bn, hy_issuance_bn, total_bn]
    Source: static_corp_issuance_annual  (data/corp_issuance_annual.csv)
    Coverage: 2015 onward. Used in §2 long-term trend chart.
    """
    q = f"""
        SELECT year, ig_issuance_bn, hy_issuance_bn,
               ig_issuance_bn + hy_issuance_bn AS total_bn
        FROM {_tbl("static_corp_issuance_annual")}
        ORDER BY year
    """
    return _bq(q)


# ==========================================
# §2 — Corporate bond & credit rating helpers
# ==========================================


def get_rating_oas_latest() -> pd.DataFrame:
    """
    Latest OAS value for each rating bucket (AAA→CCC).
    Returns: [series_key, description, value, date]
    Source: fred_daily_raw, section = 's2_ratings'
    """
    q = f"""
        WITH ranked AS (
            SELECT series_key, description, value, date,
                   ROW_NUMBER() OVER (PARTITION BY series_key ORDER BY date DESC) AS rn
            FROM {_tbl("fred_daily_raw")}
            WHERE section = 's2_ratings'
        )
        SELECT series_key, description, value, date
        FROM ranked WHERE rn = 1
        ORDER BY value
    """
    return _bq(q)


def get_rating_oas_history(
    series_keys: list | None = None,
    start_date: str = "2000-01-01",
) -> pd.DataFrame:
    """
    OAS history for rating buckets (wide format).
    Returns: [date, aaa_oas, aa_oas, a_oas, bbb_oas, bb_oas, b_oas, ccc_oas]

    SQL pushdown: date filter and series filter applied in BigQuery so only
    the required rows are transferred over the network.
    """
    series_clause = ""
    if series_keys:
        keys_str = ", ".join(f"'{k}'" for k in series_keys)
        series_clause = f"AND series_key IN ({keys_str})"

    q = f"""
        SELECT date, series_key, value
        FROM {_tbl("fred_daily_raw")}
        WHERE section = 's2_ratings'
          AND date >= '{start_date}'
          {series_clause}
        ORDER BY date, series_key
    """
    long = _bq(q)
    return long.pivot(index="date", columns="series_key", values="value").reset_index()  # noqa: PD010


def get_ig_hy_oas_history(start_date: str = "2000-01-01") -> pd.DataFrame:
    """
    Headline IG and HY OAS daily history.
    Returns: [date, ig_oas, hy_oas, ig_yield, hy_yield]
    """
    q = f"""
        SELECT date, series_key, value
        FROM {_tbl("fred_daily_raw")}
        WHERE series_key IN ('ig_oas','hy_oas','ig_yield','hy_yield')
          AND date >= '{start_date}'
        ORDER BY date, series_key
    """
    long = _bq(q)
    return long.pivot(index="date", columns="series_key", values="value").reset_index()  # noqa: PD010


def get_baa_aaa_yield_history(start_date: str = "2000-01-01") -> pd.DataFrame:
    """
    Moody's Baa and Aaa corporate yield history from FRED.
    Returns: [date, baa_yield, aaa_yield, baa_aaa_spread]
    """
    q = f"""
        SELECT date, series_key, value
        FROM {_tbl("fred_daily_raw")}
        WHERE series_key IN ('baa_yield', 'aaa_yield')
          AND date >= '{start_date}'
        ORDER BY date, series_key
    """
    long = _bq(q)
    if long.empty:
        return pd.DataFrame()
    df = long.pivot(index="date", columns="series_key", values="value").reset_index()  # noqa: PD010
    if {"baa_yield", "aaa_yield"}.issubset(df.columns):
        df["baa_aaa_spread"] = df["baa_yield"] - df["aaa_yield"]
    return df


def get_recession_periods() -> pd.DataFrame:
    """
    NBER US recession periods covering dashboard data since 2000.
    Static because these are cycle chronology dates, not market data.
    """
    return pd.DataFrame(
        [
            ("2001-03-01", "2001-11-30"),
            ("2007-12-01", "2009-06-30"),
            ("2020-02-01", "2020-04-30"),
        ],
        columns=["start", "end"],
    ).assign(start=lambda x: pd.to_datetime(x["start"]), end=lambda x: pd.to_datetime(x["end"]))


def get_moodys_defaults() -> pd.DataFrame:
    """
    Annual IG / SG default rates 1981-2024.
    Source: S&P 2024 Annual Default Study (Table 1).
    Returns: [year, sg_default_rate, ig_default_rate, ...]
    """
    return _bq(f"SELECT * FROM {_tbl('static_default_rates')} ORDER BY year")


def get_avg_cumulative_default_rates() -> pd.DataFrame:
    """
    Average cumulative default rates by rating, 1-10 year horizons.
    Source: S&P 2024 Annual Default Study Table 7/8 (1981-2024 avg).
    Returns: [rating, yr1, yr2, yr3, yr4, yr5, yr7, yr10, grade]
    """
    return _bq(f"""
        SELECT rating, yr1, yr2, yr3, yr4, yr5, yr7, yr10, grade
        FROM {_tbl("static_avg_cumulative_default_rates")}
        ORDER BY yr5 ASC
    """)


# ==========================================
# Calculations
# ==========================================


def compute_spread_zscore(series: pd.Series, window: int = 252) -> pd.Series:
    """
    Rolling z-score: (x - rolling_mean) / rolling_std.
    Default window = 252 trading days ≈ 1 year.
    """
    roll = series.rolling(window, min_periods=window // 2)
    return (series - roll.mean()) / roll.std()


def compute_spread_percentile(series: pd.Series, lookback_years: int = 10) -> float:
    """Current spread percentile vs trailing N-year history (0-100)."""
    cutoff = series.index[-1] - pd.DateOffset(years=lookback_years)
    history = series.loc[series.index >= cutoff].dropna()
    if history.empty:
        return np.nan
    current = series.dropna().iloc[-1]
    return round(float((history < current).mean() * 100), 1)


def compute_rolling_vol(series: pd.Series, window: int = 30) -> pd.Series:
    """30-day rolling std of daily spread changes (annualised)."""
    return series.diff().rolling(window).std() * np.sqrt(252)


def yoy_change(df: pd.DataFrame, col: str) -> float:
    """YoY % change for the most recent value vs same period last year."""
    df = df.dropna(subset=[col]).copy()
    if len(df) < 2:  # noqa: PLR2004
        return np.nan
    latest = df.iloc[-1]
    one_yr_ago = df[df["date"] <= latest["date"] - pd.DateOffset(years=1)]
    if one_yr_ago.empty:
        return np.nan
    prev = one_yr_ago.iloc[-1][col]
    return round((latest[col] - prev) / abs(prev) * 100, 1) if prev else np.nan


def regime_flag(percentile: float) -> tuple[str, str]:
    """
    Returns (label, color_hex) based on spread percentile.
    Used for KPI badge coloring in Streamlit.
    """
    if percentile >= 75:  # noqa: PLR2004
        return "Wide — stressed", "#A32D2D"
    elif percentile >= 50:  # noqa: PLR2004
        return "Above median", "#BA7517"
    elif percentile >= 25:  # noqa: PLR2004
        return "Below median", "#3B6D11"
    else:
        return "Tight — rich", "#185FA5"


def generate_outlook(
    ig_z: float,
    hy_z: float,
    ig_pct: float,
    hy_pct: float,
    ig_oas: float,
    hy_oas: float,
    baa_aaa_trend: float | None = None,
    default_trend: float | None = None,
) -> tuple[str, str, str, list[str]]:
    """
    Rule-based market signal from valuation, quality dispersion, and default trend.
    Returns (headline, body, border_color, tags).
    """
    ig_label, _ = regime_flag(ig_pct)
    hy_label, _ = regime_flag(hy_pct)
    tags = [
        f"IG: {ig_label}",
        f"HY: {hy_label}",
        f"IG z: {ig_z:+.1f}",
        f"HY z: {hy_z:+.1f}",
        f"HY-IG: {hy_oas - ig_oas:.0f} bp",
    ]
    if baa_aaa_trend is not None and not np.isnan(baa_aaa_trend):
        tags.append(f"Baa-Aaa 3m: {baa_aaa_trend:+.2f} pp")
    if default_trend is not None and not np.isnan(default_trend):
        tags.append(f"SG defaults YoY: {default_trend:+.1f} pp")

    quality_widening = baa_aaa_trend is not None and not np.isnan(baa_aaa_trend) and baa_aaa_trend > 0.15
    default_worsening = default_trend is not None and not np.isnan(default_trend) and default_trend > 0.75
    quality_improving = baa_aaa_trend is not None and not np.isnan(baa_aaa_trend) and baa_aaa_trend < -0.15
    default_improving = default_trend is not None and not np.isnan(default_trend) and default_trend < -0.75

    if hy_z >= 1.5 and (quality_widening or default_worsening):
        return (
            "Defensive credit: spread stress is backed by macro deterioration",
            "HY is cheapening versus its own history while lower-quality IG dispersion or realized defaults are moving the wrong way. Favor quality, reduce CCC risk, and keep liquidity for forced-selling opportunities.",
            "#A32D2D",
            tags,
        )
    if hy_z >= 1.5:
        return (
            "HY stress without full macro confirmation",
            "HY spreads are elevated, but the macro confirmation is mixed. Treat weakness as selective rather than systemic: BB carry can be attractive, while weak single-B and CCC require tighter underwriting.",
            "#BA7517",
            tags,
        )
    if hy_z <= -1.5 and ig_z <= -1.0 and not default_worsening:
        return (
            "Credit looks rich: trim beta and wait for better entry",
            "Spreads are compressed across the stack and defaults are not forcing a risk premium. Avoid chasing incremental yield; prefer benchmark weight or up-in-quality positioning.",
            "#185FA5",
            tags,
        )
    if hy_pct > 50 and ig_pct < 40:
        return (
            "IG-HY divergence: market is repricing credit quality",
            "IG remains tight while HY trades wider than median. This favors relative-value work around the BBB-BB boundary rather than a broad beta call.",
            "#BA7517",
            tags,
        )
    if quality_improving and default_improving:
        return (
            "Fundamentals easing: carry environment improving",
            "Quality dispersion and default rates are moving in the right direction. Maintain carry exposure, with a bias to credits where spread still pays for downgrade risk.",
            "#3B6D11",
            tags,
        )
    return (
        "Credit markets in normal range",
        "Spreads, dispersion, and default trends are not sending a strong tactical signal. Stay close to benchmark risk and use issuer-level work for alpha.",
        "#3B6D11",
        tags,
    )


# ==========================================
# Static reference data (no BQ needed)
# ==========================================

RATING_TABLE = [
    # (fitch, sp, moodys, description, grade, risk_level)
    ("AAA", "AAA", "Aaa", "Minimal credit risk", "IG", 1),
    ("AA+", "AA+", "Aa1", "Very low credit risk", "IG", 2),
    ("AA", "AA", "Aa2", "Very low credit risk", "IG", 2),
    ("AA-", "AA-", "Aa3", "Very low credit risk", "IG", 2),
    ("A+", "A+", "A1", "Low credit risk", "IG", 3),
    ("A", "A", "A2", "Low credit risk", "IG", 3),
    ("A-", "A-", "A3", "Low credit risk", "IG", 3),
    ("BBB+", "BBB+", "Baa1", "Moderate credit risk", "IG", 4),
    ("BBB", "BBB", "Baa2", "Moderate credit risk", "IG", 4),
    ("BBB-", "BBB-", "Baa3", "Moderate credit risk — IG/HY boundary", "IG", 4),
    ("BB+", "BB+", "Ba1", "Substantial credit risk", "HY", 5),
    ("BB", "BB", "Ba2", "Substantial credit risk", "HY", 5),
    ("BB-", "BB-", "Ba3", "Substantial credit risk", "HY", 5),
    ("B+", "B+", "B1", "High credit risk", "HY", 6),
    ("B", "B", "B2", "High credit risk", "HY", 6),
    ("B-", "B-", "B3", "High credit risk", "HY", 6),
    ("CCC+", "CCC+", "Caa1", "Very high credit risk", "HY", 7),
    ("CCC", "CCC", "Caa2", "Very high credit risk", "HY", 7),
    ("CCC-", "CCC-", "Caa3", "Very high credit risk", "HY", 7),
    ("CC", "CC", "Ca", "In or near default, possibility of recovery", "HY", 8),
    ("C", "C", "C", "In default, little chance of recovery", "HY", 9),
    ("D", "SD/D", "—", "In default", "HY", 9),
]

RATING_DF = pd.DataFrame(RATING_TABLE, columns=["fitch", "sp", "moodys", "description", "grade", "risk_level"])

# Average 5Y cumulative default rates by broad rating (S&P 1981-2024 historical avg, %)
# Source: S&P 2024 Annual Global Corporate Default and Rating Transition Study, Table 7
DEFAULT_RATES_5Y = {
    "AAA": 0.35,
    "AA": 0.26,
    "A": 0.51,
    "BBB": 1.60,
    "BB": 6.48,
    "B": 18.14,
    "CCC/C": 50.92,
}
