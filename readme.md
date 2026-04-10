# US Corporate Credit Risk Dashboard

## Project structure

```
dashboard/
├── app.py                              # Home page (Streamlit entry point)
├── data_load.py                        # BigQuery ingestion
├── data_utils.py                       # All BQ queries + calculation functions
├── requirements.txt
├── data/                               # Static CSVs
│   ├── global_fi_outstanding.csv
│   ├── us_fi_outstanding.csv
│   ├── corp_issuance_monthly.csv
│   ├── corp_issuance_annual.csv
│   ├── moodys_default_rates.csv
│   └── avg_cumulative_default_rates.csv
└── pages/
    ├── 1_market_overview.py
    ├── 2_credit_ratings.py
    └── 5_spreads_risk.py
```

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env          # fill in FRED_API_KEY and GCP_PROJECT_ID
gcloud auth application-default login
bq mk --dataset sipa-adv-c-sleepy-narwhal:credit_risk_data
python data_load.py
streamlit run app.py
```

---

## BigQuery tables

| Table | Source file / API | Frequency |
|---|---|---|
| `fred_daily_raw` | FRED API (13 OAS + yield series) | Daily — GitHub Actions |
| `fred_quarterly_raw` | FRED API (5 Z.1 outstanding series) | Daily — GitHub Actions |
| `static_global_fi` | `data/global_fi_outstanding.csv` | Annually (July) |
| `static_us_fi_structure` | `data/us_fi_outstanding.csv` | Quarterly |
| `static_corp_issuance_monthly` | `data/corp_issuance_monthly.csv` | Monthly |
| `static_corp_issuance_annual` | `data/corp_issuance_annual.csv` | Annually |
| `static_default_rates` | `data/moodys_default_rates.csv` | Annually (March) |
| `static_avg_cumulative_default_rates` | `data/avg_cumulative_default_rates.csv` | Annually (March) |

---

## Static CSV formats

| File | Source | URL | Columns | Notes |
|---|---|---|---|---|
| `global_fi_outstanding.csv` | SIFMA Fact Book Tab 1-09 | [sifma.org/fact-book](https://www.sifma.org/research/statistics/fact-book) | `year, us, eu, china, japan, uk, australia, canada, hk, singapore, switzerland, dm, em, total` | Values in $bn with thousand-separator commas — handled automatically |
| `us_fi_outstanding.csv` | SIFMA US FI Statistics Tab 1 (Annual) | [sifma.org/us-fi-stats](https://www.sifma.org/research/statistics/us-fixed-income-securities-statistics) | Raw: `UST, MBS, Corporates, Munis, Agency, ABS, CP` → renamed on ingest | MBS and ABS are `n/a` from 2022 onward → stored as NaN, handled gracefully |
| `corp_issuance_monthly.csv` | SIFMA Corp Bonds Tab 1 (Monthly) | [sifma.org/corp-bonds](https://www.sifma.org/research/statistics/us-corporate-bonds-statistics) | `date (YY-Mon), ig_issuance_bn, hy_issuance_bn` | Date `"25-Mar"` → parsed to `2025-03-01` automatically. Coverage: Mar 2025+ |
| `corp_issuance_annual.csv` | SIFMA Corp Bonds Tab 1 (Annual) | [sifma.org/corp-bonds](https://www.sifma.org/research/statistics/us-corporate-bonds-statistics) | `year, ig_issuance_bn, hy_issuance_bn` | Coverage: 2015+. Values may have thousand-separator commas |
| `moodys_default_rates.csv` | S&P Annual Default Study Table 1 | [PDF (public)](https://maalot.co.il/Publications/FTS20250331162126.pdf) | `year, sg_default_rate, ig_default_rate` | Annual rates 1981–2024. Despite the filename, source is S&P (not Moody's) |
| `avg_cumulative_default_rates.csv` | S&P Annual Default Study Tables 7–8 | [PDF (public)](https://maalot.co.il/Publications/FTS20250331162126.pdf) | `rating, yr1, yr2, yr3, yr4, yr5, yr7, yr10, grade` | 1981–2024 issuer-weighted avg cumulative default rates by rating |

---

## FRED API series

All pulled automatically by `data_load.py`. Free key: https://fred.stlouisfed.org/docs/api/api_key.html

| Key | Series ID | Description | Section |
|---|---|---|---|
| `ig_oas` | `BAMLC0A0CM` | IG OAS — ICE BofA US Corporate Index | §5 |
| `hy_oas` | `BAMLH0A0HYM2` | HY OAS — ICE BofA HY Master II | §5 |
| `ig_yield` | `BAMLC0A0CMEY` | IG Effective Yield | §5 |
| `hy_yield` | `BAMLH0A0HYM2EY` | HY Effective Yield | §5 |
| `aaa_oas` | `BAMLC0A1CAAA` | AAA IG OAS | §2 |
| `aa_oas` | `BAMLC0A2CAA` | AA IG OAS | §2 |
| `a_oas` | `BAMLC0A3CA` | A IG OAS | §2 |
| `bbb_oas` | `BAMLC0A4CBBB` | BBB IG OAS | §2 |
| `bb_oas` | `BAMLH0A1HYBB` | BB HY OAS | §2 |
| `b_oas` | `BAMLH0A2HYB` | B HY OAS | §2 |
| `ccc_oas` | `BAMLH0A3HYC` | CCC & Lower HY OAS | §2 |
| `baa_yield` | `BAA` | Moody's Baa Corporate Bond Yield | §5 |
| `aaa_yield` | `AAA` | Moody's Aaa Corporate Bond Yield | §5 |
| `corp_outstanding` | `NCBDBIQ027S` | Nonfinancial Corp Debt Securities ($mn) | §1 |
| `tsy_outstanding` | `GFDEBTN` | Federal Debt: Total Public Debt ($mn) | §1 |
| `muni_outstanding` | `SLGSDODNS` | State & Local Govt Debt Securities ($mn) | §1 |
| `agency_outstanding` | `FGSDODNS` | Federal Govt Debt Securities incl Agency ($mn) | §1 |

---

## Streamlit secrets (deployed app)

Settings → Secrets in Streamlit Community Cloud:

```toml
[gcp_service_account]
type = "service_account"
project_id = "sipa-adv-c-sleepy-narwhal"
private_key_id = "..."
private_key = "-----BEGIN RSA PRIVATE KEY-----\n..."
client_email = "streamlit@sipa-adv-c-sleepy-narwhal.iam.gserviceaccount.com"
client_id = "..."
```

---

## GitHub Actions (daily auto-ingestion)

Create `.github/workflows/data_load.yml`:

```yaml
name: Daily data ingestion
on:
  schedule:
    - cron: '0 6 * * *'
  workflow_dispatch:

jobs:
  ingest:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.11' }
      - run: pip install -r requirements.txt
      - run: python data_load.py
        env:
          FRED_API_KEY: ${{ secrets.FRED_API_KEY }}
          GCP_PROJECT_ID: sipa-adv-c-sleepy-narwhal
          GOOGLE_APPLICATION_CREDENTIALS_JSON: ${{ secrets.GCP_SA_KEY }}
```

Add `FRED_API_KEY` and `GCP_SA_KEY` to GitHub → Settings → Secrets and variables → Actions.