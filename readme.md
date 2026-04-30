<p align="center">
  <img src="assets/sleepy-narwhal.png" alt="Sleepy Narwhal Advanced Computing" width="700">
</p>

# US Corporate Credit Risk Dashboard

An interactive Streamlit dashboard for monitoring US corporate credit risk across investment-grade (IG) and high-yield (HY) markets. The app is designed for students learning credit analysis and for junior credit analysts who need a fast, structured way to answer:

> Are current corporate credit conditions normal, rich, or stressed, and what evidence supports that view?

The dashboard combines FRED market data, SIFMA market-structure data, and S&P default-rate data into a multi-page analytical workflow. It moves from a five-second executive signal to deeper spread-regime, rating-curve, macro-risk, and strategy views.

## Target Users

The project was repositioned from a general data-visualization idea into a credit-analysis tool with a clearer audience.

- Students can use it to learn how credit analysts read spreads, rating buckets, default rates, and market regimes.
- Credit analysts can use it as a quick briefing tool before deeper issuer-level research.
- Instructors or presenters can use it to explain how raw market data becomes an analytical signal.

## App Logic

The app follows a simple credit-analysis flow:

1. **Executive Dashboard** (`app.py`)
   - Shows the latest IG OAS, HY OAS, HY-IG spread, HY z-score, and regime label.
   - Generates a rule-based strategy signal from spread levels, percentiles, quality dispersion, and default trends.
   - Gives the user a quick answer before they open the deeper pages.

2. **Spread Regime** (`pages/1_spread_regime.py`)
   - Compares IG and HY OAS against history.
   - Uses rolling z-scores and trailing percentile ranks to classify whether spreads are tight, normal, or stressed.
   - Adds NBER recession shading so the user can compare current conditions with past stress periods.

3. **Credit Curve** (`pages/2_credit_curve.py`)
   - Breaks spreads down by rating bucket from AAA to CCC.
   - Compares current rating-level OAS with five-year averages.
   - Connects current spread compensation with historical cumulative default rates.

4. **Spread vs Macro** (`pages/5_spreads_risk.py`)
   - Tests whether spread widening is supported by macro or fundamental deterioration.
   - Compares HY OAS with speculative-grade default rates.
   - Tracks the Baa-Aaa spread as a quality-dispersion and credit-stress indicator.

5. **Strategy Outlook** (`pages/6_strategy_outlook.py`)
   - Synthesizes spread levels, z-scores, percentiles, yields, and default-risk data.
   - Produces a rule-based market view for IG and HY credit positioning.

## Project Structure

```text
sleepy-narwhal/
|-- app.py                         # Streamlit home page / executive dashboard
|-- data_load.py                   # FRED + CSV ingestion into BigQuery
|-- data_utils.py                  # BigQuery query helpers and calculation functions
|-- DATA_LOADING.md                # Detailed data-loading and performance notes
|-- requirements.txt               # Python dependencies
|-- test_data_utils.py             # Unit tests for utility calculations
|-- data/
|   |-- avg_cumulative_default_rates.csv
|   |-- corp_issuance_annual.csv
|   |-- corp_issuance_monthly.csv
|   |-- global_fi_outstanding.csv
|   |-- moodys_default_rates.csv
|   |-- us_fi_outstanding.csv
|-- pages/
|   |-- 1_spread_regime.py
|   |-- 2_credit_curve.py
|   |-- 5_spreads_risk.py
|   |-- 6_strategy_outlook.py
|-- utils/
|   |-- perf.py                    # Page load timing and optional profiling helpers
|   |-- style.py                   # Shared CSS and custom sidebar navigation
```

## Data Pipeline

The data pipeline separates live market time series from small static reference datasets.

### 1. FRED API to BigQuery

`data_load.py` pulls daily and quarterly FRED series into BigQuery:

- IG and HY option-adjusted spreads (OAS)
- IG and HY effective yields
- Rating-level OAS from AAA through CCC
- Moody's Aaa and Baa corporate bond yields
- Fixed-income outstanding series from Fed Z.1 data

FRED tables use incremental loading. Each run checks the latest stored date in BigQuery and only appends new observations.

### 2. Static CSVs to BigQuery

Small curated CSV files in `data/` are uploaded with full table replacement. This keeps BigQuery synchronized with the repo version of each file.

Static datasets include:

- Global fixed-income outstanding by region
- US fixed-income market structure
- Corporate issuance
- Annual speculative-grade and investment-grade default rates
- Average cumulative default rates by rating bucket

### 3. Streamlit Reads from BigQuery

The Streamlit app does not call FRED directly. Pages read prepared data from BigQuery through helper functions in `data_utils.py`, which makes page loads more predictable and avoids API dependency during user sessions.

## Main Functions

### Data Access

- `_bq_client()` creates an authenticated BigQuery client for either Streamlit Cloud secrets or local Google Application Default Credentials.
- `_bq(query)` runs a SQL query and returns a pandas DataFrame.
- `_tbl(name)` builds fully qualified BigQuery table names.
- `get_ig_hy_oas_history()` returns headline IG/HY OAS and yield history in wide format.
- `get_rating_oas_latest()` returns the latest OAS value for each rating bucket.
- `get_rating_oas_history()` returns rating-level OAS history.
- `get_baa_aaa_yield_history()` returns Aaa and Baa yields and computes the Baa-Aaa spread.
- `get_moodys_defaults()` returns annual default-rate data.
- `get_avg_cumulative_default_rates()` returns cumulative default-rate assumptions by rating.

### Calculations

- `compute_spread_zscore(series, window=252)` calculates a rolling one-year z-score.
- `compute_spread_percentile(series, lookback_years=10)` calculates the latest spread percentile versus trailing history.
- `compute_rolling_vol(series, window=30)` calculates annualized rolling volatility of spread changes.
- `yoy_change(df, col)` calculates year-over-year percentage change for a selected column.
- `regime_flag(percentile)` converts a spread percentile into a regime label and color.
- `generate_outlook(...)` combines valuation, spread dispersion, and default trends into a rule-based strategy signal.

### UI and Performance

- `inject_css()` applies the shared visual system.
- `render_sidebar()` creates consistent navigation across pages.
- `display_load_time()` shows render time at the bottom of each page.
- `profile_page()` can be used during development to diagnose slow code paths with `cProfile`.

## Performance Optimizations

The project includes several optimizations to improve speed, code clarity, and user experience:

- **SQL pushdown:** Filtering, latest-value selection, and simple calculations happen in BigQuery before data reaches pandas.
- **Streamlit caching:** Page-level `@st.cache_data` wrappers reduce repeated BigQuery calls during user navigation.
- **Incremental ingestion:** FRED time series append only new rows instead of reloading full history every day.
- **Wide-format pivots:** Query helpers return analysis-ready DataFrames so page code stays focused on charts and interpretation.
- **Shared styling:** Common CSS and sidebar logic live in `utils/style.py`, which keeps page files cleaner and visually consistent.
- **Load-time measurement:** `display_load_time()` makes performance visible during development and presentation.

## Setup

Install dependencies:

```bash
pip install -r requirements.txt
```

Authenticate with Google Cloud for local development:

```bash
gcloud auth application-default login
```

Load or refresh data:

```bash
python data_load.py
```

Run the Streamlit app:

```bash
streamlit run app.py
```

## BigQuery Tables

Dataset: `sipa-adv-c-sleepy-narwhal.credit_risk_data`

| Table | Source | Loading strategy |
|---|---|---|
| `fred_daily_raw` | FRED daily OAS and yield series | Incremental append |
| `fred_quarterly_raw` | FRED quarterly outstanding series | Incremental append |
| `static_global_fi` | `data/global_fi_outstanding.csv` | Full replace |
| `static_us_fi_structure` | `data/us_fi_outstanding.csv` | Full replace |
| `static_corp_issuance_monthly` | `data/corp_issuance_monthly.csv` | Full replace |
| `static_corp_issuance_annual` | `data/corp_issuance_annual.csv` | Full replace |
| `static_default_rates` | `data/moodys_default_rates.csv` | Full replace |
| `static_avg_cumulative_default_rates` | `data/avg_cumulative_default_rates.csv` | Full replace |

## Tests and Quality

Run tests:

```bash
pytest
```

The test suite focuses on calculation helpers in `data_utils.py`, including z-scores, percentiles, rolling volatility, year-over-year change, regime classification, and outlook generation.

## Project Presentation Outline

1. **Initial Proposal**
   - Introduce the original project proposal.
   - Reflect on the problems with the initial proposal:
     - The dataset was chosen mainly because it seemed simple.
     - The final project goal was not clearly defined.

2. **New Proposal**
   - Explain the new proposal: a US corporate credit risk dashboard.
   - Define the target user:
     - Students learning credit analysis.
     - Credit analysts.
   - Analyze what credit analysts need and when they would use this tool.

3. **Live App Walkthrough**
   - Walk through each page of the live app.
   - Explain why each part exists.
   - Explain how the pages connect to each other in the credit-analysis workflow.

4. **Code Walkthrough**
   - Walk through the project by file structure.
   - Explain how the files are organized.
   - Introduce the main functions:
     - What each function does.
     - How the functions work together.
   - Show how the code logic supports the project goal.
   - Explain the optimizations made in the project.
   - Explain how these optimizations improve performance, including:
     - Faster runtime.
     - Clearer code structure.
     - Better user experience.

5. **What We Learned**
   - Main takeaways:
     - Set up a clear goal.
     - Define the target user.
     - The first version does not need to be perfect.
     - Always polish and improve.
