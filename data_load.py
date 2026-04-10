"""
data_load.py
============
Pulls all required data into BigQuery for the US Credit Risk Dashboard.

BigQuery tables created:
  fred_daily_raw       — daily FRED series (OAS, yields, spreads)
  fred_quarterly_raw   — quarterly FRED series (outstanding, debt levels)
  static_us_fi_structure     — US fixed income market structure by asset class (CSV)
  static_global_fi           — Global FI outstanding by region 2010-2024 (CSV)
  static_corp_issuance       — IG/HY gross issuance monthly (CSV)
  static_moodys_defaults     — Moody's annual default rates by rating (CSV)

Run locally:
  python data_load.py

GitHub Actions (daily cron) runs the same command.
Auth: local uses gcloud ADC; Actions uses service account JSON secret.
"""

import datetime
import logging
import os

import pandas as pd
import pandas_datareader.data as web
from dotenv import load_dotenv
from google.cloud import bigquery

load_dotenv()

# ==========================================
# 1. Configuration
# ==========================================
PROJECT_ID = "sipa-adv-c-sleepy-narwhal"
DATASET_ID = "credit_risk_data"
FRED_API_KEY = os.environ.get("FRED_API_KEY", "449c21ccb425167e72778c12cf10b63f")
HISTORY_START = datetime.datetime(2000, 1, 1)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)-8s %(message)s")
log = logging.getLogger(__name__)

# ==========================================
# 2. FRED series catalogue
# ==========================================

# --- Daily series ---
FRED_DAILY = {
    # §5 Headline spreads (OAS, bps)
    "ig_oas": ("BAMLC0A0CM", "IG OAS – ICE BofA US Corporate Index", "s5_spreads"),
    "hy_oas": ("BAMLH0A0HYM2", "HY OAS – ICE BofA HY Master II", "s5_spreads"),
    # §5 Effective yields (%)
    "ig_yield": ("BAMLC0A0CMEY", "IG Effective Yield", "s5_spreads"),
    "hy_yield": ("BAMLH0A0HYM2EY", "HY Effective Yield", "s5_spreads"),
    # §2 Rating-level OAS – IG buckets
    "aaa_oas": ("BAMLC0A1CAAA", "AAA IG OAS", "s2_ratings"),
    "aa_oas": ("BAMLC0A2CAA", "AA IG OAS", "s2_ratings"),
    "a_oas": ("BAMLC0A3CA", "A IG OAS", "s2_ratings"),
    "bbb_oas": ("BAMLC0A4CBBB", "BBB IG OAS", "s2_ratings"),
    # §2 Rating-level OAS – HY buckets
    "bb_oas": ("BAMLH0A1HYBB", "BB HY OAS", "s2_ratings"),
    "b_oas": ("BAMLH0A2HYB", "B HY OAS", "s2_ratings"),
    "ccc_oas": ("BAMLH0A3HYC", "CCC & Lower HY OAS", "s2_ratings"),
    # §5 Moody's legacy yields (long history proxy)
    "baa_yield": ("BAA", "Moody's Baa Corporate Bond Yield", "s5_spreads"),
    "aaa_yield": ("AAA", "Moody's Aaa Corporate Bond Yield", "s5_spreads"),
}

# --- Quarterly series (Fed Z.1 Flow of Funds) ---
FRED_QUARTERLY = {
    # §1 US fixed income outstanding by asset class
    "tsy_outstanding": ("GFDEBTN", "Federal Debt: Total Public Debt ($mn)", "s1_outstanding"),
    "corp_outstanding": (
        "NCBDBIQ027S",
        "Nonfinancial Corp Debt Securities ($mn)",
        "s1_outstanding",
    ),
    "muni_outstanding": ("SLGSDODNS", "State & Local Govt Debt Securities ($mn)", "s1_outstanding"),
    "agency_outstanding": (
        "FGSDODNS",
        "Federal Govt Debt Securities incl Agency ($mn)",
        "s1_outstanding",
    ),
    # §2 Corporate debt for trend chart
    "corp_debt_total": ("BCNSDODNS", "Nonfinancial Corp Debt Securities+Loans ($mn)", "s2_corp"),
}

# ==========================================
# 3. BigQuery helpers
# ==========================================


def bq_client():
    return bigquery.Client(project=PROJECT_ID)


def table_id(name):
    return f"{PROJECT_ID}.{DATASET_ID}.{name}"


def latest_date(client, tbl, col="date"):
    try:
        client.get_table(table_id(tbl))
    except Exception:
        return None
    row = next(iter(client.query(f"SELECT MAX({col}) AS d FROM `{table_id(tbl)}`").result()))
    return row["d"]


def write_bq(client, df, tbl, mode="WRITE_APPEND"):
    cfg = bigquery.LoadJobConfig(
        write_disposition=mode,
        autodetect=True,
        create_disposition="CREATE_IF_NEEDED",
    )
    job = client.load_table_from_dataframe(df, table_id(tbl), job_config=cfg)
    job.result()
    log.info("  → %d rows written to %s", len(df), tbl)


# ==========================================
# 4. FRED fetch
# ==========================================


def fetch_fred(series_map, start, end):
    """Pull multiple FRED series → long-format DataFrame."""
    ids = [v[0] for v in series_map.values()]
    keys = list(series_map.keys())
    log.info("Fetching %d FRED series %s → %s", len(ids), start.date(), end.date())

    raw = web.DataReader(ids, "fred", start, end, api_key=FRED_API_KEY)
    raw.index.name = "date"
    raw.columns = keys  # rename fred ids → our keys

    long = (
        raw.reset_index()
        .melt(id_vars="date", var_name="series_key", value_name="value")
        .dropna(subset=["value"])
    )

    long["fred_id"] = long["series_key"].map({k: v[0] for k, v in series_map.items()})
    long["description"] = long["series_key"].map({k: v[1] for k, v in series_map.items()})
    long["section"] = long["series_key"].map({k: v[2] for k, v in series_map.items()})
    long["loaded_at"] = datetime.datetime.utcnow()
    return long[["date", "series_key", "fred_id", "value", "description", "section", "loaded_at"]]


def incremental_start(client, tbl, fallback):
    ld = latest_date(client, tbl)
    if ld:
        start = datetime.datetime.combine(ld, datetime.time()) + datetime.timedelta(days=1)
        log.info("%s: incremental from %s", tbl, start.date())
    else:
        start = fallback
        log.info("%s: full load from %s", tbl, start.date())
    return start


# ==========================================
# 5. Static CSV loaders
# ==========================================


def _load_csv(path, label):
    if not os.path.exists(path):
        log.warning("CSV not found: %s — skipping %s", path, label)
        return None
    df = pd.read_csv(path)
    df.columns = [c.lower().strip().replace(" ", "_") for c in df.columns]
    df["loaded_at"] = datetime.datetime.utcnow()
    log.info("Loaded %s: %d rows", label, len(df))
    return df


def load_global_fi_csv():
    """
    data/global_fi_outstanding.csv — SIFMA Capital Markets Fact Book Tab 1-09.

    Raw columns : year, Australia, Canada, China, EU, HK, Japan, Singapore,
                  Switzerland, UK, US, DM, EM, Total
    Numbers     : thousand-separator commas ("1,884.7") — handled by thousands=','
    Output cols : lowercased to match COLORS / REGION_LABELS keys in section1:
                  year, australia, canada, china, eu, hk, japan, singapore,
                  switzerland, uk, us, dm, em, total

    Download: https://www.sifma.org/research/statistics/fact-book  (Tab 1-09)
    """
    path = "data/global_fi_outstanding.csv"
    if not os.path.exists(path):
        log.warning("CSV not found: %s — skipping global_fi_outstanding", path)
        return None

    # thousands=',' handles "1,884.7" → 1884.7 at parse time (no manual cleaning needed)
    df = pd.read_csv(path, thousands=",")
    df.columns = [c.lower().strip() for c in df.columns]  # Australia → australia, US → us …
    df["loaded_at"] = datetime.datetime.utcnow()

    log.info("Loaded global_fi_outstanding: %d rows, columns: %s", len(df), list(df.columns))
    return df


def load_us_fi_structure_csv():
    """
    data/us_fi_outstanding.csv — SIFMA US Fixed Income Securities Statistics, Tab 1 (Annual).

    Raw columns : (unnamed year), UST, MBS, Corporates, Munis, Agency, ABS, CP
    Issues      : • unnamed first column (year)
                  • thousand-separator commas  →  thousands=','
                  • 'n/a' strings for missing MBS/ABS post-2021  →  na_values
    Rename map  : UST→treasury_bn, MBS→mbs_bn, Corporates→corporate_bn,
                  Munis→municipal_bn, Agency→agency_bn, ABS→abs_bn, CP→money_market_bn
    Units       : $bn (as published by SIFMA)

    NaN policy  : MBS and ABS are NaN from 2022 onward in the source.
                  We keep them as NaN — the donut chart and KPI cards use
                  the most recent non-NaN value per column independently.

    Download    : https://www.sifma.org/research/statistics/us-fixed-income-securities-statistics
    """
    path = "data/us_fi_outstanding.csv"
    if not os.path.exists(path):
        log.warning("CSV not found: %s — skipping us_fi_structure", path)
        return None

    df = pd.read_csv(
        path,
        thousands=",",
        na_values=["n/a", "N/A", "na", "NA", "-", ""],
        index_col=0,  # unnamed first column → index
    )
    df.index.name = "year"
    df = df.reset_index()

    # Rename to standard internal column names
    df = df.rename(
        columns={
            "UST": "treasury_bn",
            "MBS": "mbs_bn",
            "Corporates": "corporate_bn",
            "Munis": "municipal_bn",
            "Agency": "agency_bn",
            "ABS": "abs_bn",
            "CP": "money_market_bn",  # Commercial Paper ≈ Money Market proxy
        }
    )

    df["loaded_at"] = datetime.datetime.utcnow()
    log.info(
        "Loaded us_fi_structure: %d rows, columns: %s — NaN counts: MBS=%d, ABS=%d",
        len(df),
        list(df.columns),
        df["mbs_bn"].isna().sum(),
        df["abs_bn"].isna().sum(),
    )
    return df


def load_corp_issuance_monthly_csv():
    """
    data/corp_issuance_monthly.csv — SIFMA US Corporate Bonds Statistics, Tab 1 (Monthly).

    Raw date format : "25-Mar", "26-Jan" (YY-Mon) -> parsed to YYYY-MM-01.
    Columns         : date, ig_issuance_bn, hy_issuance_bn
    Units           : USD billions
    Coverage        : Mar 2025 onward (update monthly)
    Used in         : §1 recent monthly issuance bar chart
    Download        : https://www.sifma.org/research/statistics/us-corporate-bonds-statistics
    """
    path = "data/corp_issuance_monthly.csv"
    if not os.path.exists(path):
        log.warning("CSV not found: %s — skipping corp_issuance_monthly", path)
        return None
    df = pd.read_csv(path, thousands=",", na_values=["", "n/a", "N/A", "-"])
    df["date"] = pd.to_datetime("20" + df["date"].astype(str).str.strip(), format="%Y-%b")
    df["loaded_at"] = datetime.datetime.utcnow()
    log.info(
        "Loaded corp_issuance_monthly: %d rows (%s -> %s)",
        len(df),
        df["date"].min().date(),
        df["date"].max().date(),
    )
    return df


def load_corp_issuance_annual_csv():
    """
    data/corp_issuance_annual.csv — SIFMA US Corporate Bonds Statistics, Tab 1 (Annual).

    Columns  : year (int), ig_issuance_bn, hy_issuance_bn
    Units    : USD billions (thousand-separator commas handled by thousands=",")
    Coverage : 2015 onward (update annually)
    Used in  : §2 long-term IG/HY issuance trend (stacked area)
    Download : https://www.sifma.org/research/statistics/us-corporate-bonds-statistics
    """
    path = "data/corp_issuance_annual.csv"
    if not os.path.exists(path):
        log.warning("CSV not found: %s — skipping corp_issuance_annual", path)
        return None
    df = pd.read_csv(path, thousands=",", na_values=["", "n/a", "N/A", "-"])
    df["loaded_at"] = datetime.datetime.utcnow()
    log.info(
        "Loaded corp_issuance_annual: %d rows (%d -> %d)",
        len(df),
        df["year"].min(),
        df["year"].max(),
    )
    return df


def load_moodys_defaults_csv():
    """
    data/moodys_default_rates.csv — Annual issuer-weighted default rates 1981-2024.

    Source: S&P Global Ratings 2024 Annual Global Corporate Default and Rating
    Transition Study (Table 1), publicly available — no login required.
    URL: https://maalot.co.il/Publications/FTS20250331162126.pdf

    Columns: year, sg_default_rate (speculative grade %), ig_default_rate (IG %),
             aaa, aa, a, bbb, bb, b, ccc  (rating-level annual default %, optional)
    """
    path = "data/moodys_default_rates.csv"
    if not os.path.exists(path):
        log.warning("CSV not found: %s — skipping default rates", path)
        return None

    df = pd.read_csv(path, na_values=["", " ", "n/a", "N/A"])
    df.columns = [c.lower().strip() for c in df.columns]
    df["loaded_at"] = datetime.datetime.utcnow()
    log.info("Loaded default_rates: %d rows", len(df))
    return df


def load_avg_cumulative_default_rates_csv():
    """
    data/avg_cumulative_default_rates.csv — Average cumulative default rates by rating.

    Source: S&P 2024 Annual Default Study Table 7/8 (1981-2024 averages).
    Columns: rating, yr1, yr2, yr3, yr4, yr5, yr7, yr10, grade, source
    Units: % (e.g. 26.78 means 26.78%)

    Used by section2 chart_default_rates() bar chart.
    Static — update once per year after S&P publishes new study (~March).
    """
    path = "data/avg_cumulative_default_rates.csv"
    if not os.path.exists(path):
        log.warning("CSV not found: %s — skipping avg cumulative default rates", path)
        return None

    df = pd.read_csv(path)
    df.columns = [c.lower().strip() for c in df.columns]
    df["loaded_at"] = datetime.datetime.utcnow()
    log.info("Loaded avg_cumulative_default_rates: %d rows", len(df))
    return df


# ==========================================
# 6. Main pipeline
# ==========================================


def run():
    log.info("=" * 55)
    log.info("US Credit Dashboard — data ingestion start")
    log.info("=" * 55)

    client = bq_client()
    today = datetime.datetime.utcnow()

    # ── FRED daily ──────────────────────────────────────────
    start_d = incremental_start(client, "fred_daily_raw", HISTORY_START)
    if start_d.date() <= today.date():
        df = fetch_fred(FRED_DAILY, start_d, today)
        if not df.empty:
            write_bq(client, df, "fred_daily_raw")
    else:
        log.info("fred_daily_raw already up to date")

    # ── FRED quarterly ───────────────────────────────────────
    start_q = incremental_start(client, "fred_quarterly_raw", HISTORY_START)
    if start_q.date() <= today.date():
        df = fetch_fred(FRED_QUARTERLY, start_q, today)
        if not df.empty:
            write_bq(client, df, "fred_quarterly_raw")
    else:
        log.info("fred_quarterly_raw already up to date")

    # ── Static CSVs (full replace each run) ─────────────────
    for loader, tbl in [
        (load_global_fi_csv, "static_global_fi"),
        (load_us_fi_structure_csv, "static_us_fi_structure"),
        (load_corp_issuance_monthly_csv, "static_corp_issuance_monthly"),
        (load_corp_issuance_annual_csv, "static_corp_issuance_annual"),
        (load_moodys_defaults_csv, "static_default_rates"),
        (load_avg_cumulative_default_rates_csv, "static_avg_cumulative_default_rates"),
    ]:
        df = loader()
        if df is not None:
            write_bq(client, df, tbl, mode="WRITE_TRUNCATE")

    log.info("=" * 55)
    log.info("Ingestion complete")
    log.info("=" * 55)


if __name__ == "__main__":
    run()
