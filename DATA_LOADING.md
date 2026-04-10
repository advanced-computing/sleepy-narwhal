# Data loading strategy

> Lab 10 documentation — US Corporate Credit Risk Dashboard

## Overview

The dashboard pulls data from two categories of source:

- **FRED API** — live, automatically updated daily via GitHub Actions
- **Static CSVs** — manually maintained files committed to the repo, uploaded to BigQuery on each `data_load.py` run

All data ultimately lives in **BigQuery** (`sipa-adv-c-sleepy-narwhal.credit_risk_data`). The Streamlit app never calls the FRED API directly — it only reads from BigQuery, which keeps page load times predictable and independent of upstream API availability.

---

## Data loading types

### 1. Incremental loading — FRED daily series

**Tables:** `fred_daily_raw`, `fred_quarterly_raw`

**Strategy:** Incremental append — each run of `data_load.py` queries BigQuery for the latest date already stored, then fetches only new data from FRED from that date forward. On the first run (empty table), a full historical load is performed from `HISTORY_START = 2000-01-01`.

**Why:** The FRED series (OAS spreads, yields, outstanding) are append-only time series. Re-fetching the full history on every run would be slow and wasteful — daily OAS history since 2000 is ~6,000 rows per series × 13 series = ~78,000 rows. Incremental loading reduces each daily run to ~1–5 new rows per series.

```python
# data_load.py — incremental pattern
latest = get_latest_date(client, "fred_daily_raw")
start = latest + timedelta(days=1) if latest else HISTORY_START
df = fetch_fred(FRED_DAILY, start, today)
write_bq(df, "fred_daily_raw", mode="WRITE_APPEND")
```

---

### 2. Full replace — static CSVs

**Tables:** `static_global_fi`, `static_us_fi_structure`, `static_corp_issuance_monthly`, `static_corp_issuance_annual`, `static_default_rates`, `static_avg_cumulative_default_rates`

**Strategy:** Full truncate-and-replace (`WRITE_TRUNCATE`) on every `data_load.py` run. The entire CSV is re-uploaded each time.

**Why:** These tables are small (< 200 rows each) and sourced from manually-curated CSV files. The source of truth is the CSV in the repo, not the BigQuery table. If someone updates a CSV (e.g. adding a new year to `corp_issuance_annual.csv`), a full replace ensures the table is always an exact mirror of the file — no partial-update edge cases. The cost of a full replace on a 50-row table is negligible.

```python
# data_load.py — full replace pattern
df = load_global_fi_csv()          # reads data/global_fi_outstanding.csv
write_bq(df, "static_global_fi", mode="WRITE_TRUNCATE")
```

---

## BigQuery table summary

| Table | Rows (approx) | Loading type | Updated |
|---|---|---|---|
| `fred_daily_raw` | ~78,000 | Incremental append | Daily (GitHub Actions) |
| `fred_quarterly_raw` | ~500 | Incremental append | Daily (GitHub Actions) |
| `static_global_fi` | 15 | Full replace | Annually (July) |
| `static_us_fi_structure` | 11 | Full replace | Quarterly |
| `static_corp_issuance_monthly` | ~13+ | Full replace | Monthly |
| `static_corp_issuance_annual` | 11 | Full replace | Annually |
| `static_default_rates` | 44 | Full replace | Annually (March) |
| `static_avg_cumulative_default_rates` | 7 | Full replace | Annually (March) |

---

## Performance: SQL pushdown

To keep page loads under 2 seconds, filtering and simple aggregations are pushed into BigQuery SQL rather than done in Python/pandas after loading all rows.

**Examples:**

```sql
-- Only fetch the latest value per rating series (not all history)
WITH ranked AS (
    SELECT series_key, value, date,
           ROW_NUMBER() OVER (PARTITION BY series_key ORDER BY date DESC) AS rn
    FROM fred_daily_raw
    WHERE section = 's2_ratings'
)
SELECT series_key, value, date FROM ranked WHERE rn = 1

-- total_bn computed in SQL — avoids a Python round-trip
SELECT year, ig_issuance_bn, hy_issuance_bn,
       ig_issuance_bn + hy_issuance_bn AS total_bn
FROM static_corp_issuance_annual
ORDER BY year

-- Date filter pushed to SQL — reduces rows for OAS history queries
SELECT date, series_key, value
FROM fred_daily_raw
WHERE section = 's2_ratings'
  AND date >= '2000-01-01'   -- ← filter in SQL, not pandas
ORDER BY date, series_key

-- Explicit column selection — excludes loaded_at and other metadata cols
SELECT year, us, eu, china, japan, uk, australia,
       canada, hk, singapore, switzerland, dm, em, total
FROM static_global_fi
ORDER BY year
```

---

## Performance: Streamlit caching

Every BigQuery query is wrapped in `@st.cache_data` at the page level. Cache TTLs are chosen based on how frequently the underlying data actually changes:

| Cached function | TTL | Reason |
|---|---|---|
| `_global_fi()` | 3600s (1h) | Annual data, only changes once a year |
| `_us_latest()` | 3600s (1h) | Quarterly data |
| `_corp_outstanding()` | 3600s (1h) | Quarterly FRED data |
| `_corp_issuance()` | 3600s (1h) | Monthly data |
| `_oas_latest()` | 3600s (1h) | Daily FRED data |
| `_oas_history()` | 3600s (1h) | Daily FRED data |
| `_avg_cum_dr()` | 86400s (24h) | Annual S&P study data |
| `_issuance()` | 86400s (24h) | Annual data |

On subsequent page loads (cache warm), all queries are served from memory — no BigQuery round-trips — which brings load times to < 0.5s.

On initial/cold page loads, the bottleneck is BigQuery network latency (~0.3–0.8s per query). With SQL pushdown reducing row counts and explicit column selection avoiding unnecessary data transfer, each query stays well under 1s.

---

## Performance measurement

Each page wraps all content in a `display_load_time()` context manager (required by Lab 10):

```python
from utils.perf import display_load_time, profile_page

_profile = st.sidebar.checkbox("Enable profiler", value=False)
_ctx = profile_page() if _profile else display_load_time()

with _ctx:
    # all page content
    ...
```

The **profiler** (`profile_page()`) uses Python's built-in `cProfile` and renders a collapsible report in the page. It is gated behind a sidebar checkbox and disabled by default — the profiler adds ~5–15% overhead and should not be left on in production.

**How to interpret profiling results:**

- **cumtime** — total time including callees. A high value here identifies the slow code path (usually a BigQuery query or network call).
- **tottime** — time only inside the function itself. High here signals a hot loop — consider vectorising with pandas or NumPy.
- **ncalls** — if unexpectedly high, the function is being called redundantly; `@st.cache_data` should help.
- Lines mentioning `bigquery`, `http`, or `grpc` are network I/O — reduce them with SQL pushdown or caching.
