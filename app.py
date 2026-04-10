"""
app.py — Home page + shared config for the US Credit Risk Dashboard.

Streamlit multi-page setup:
  app.py                          → home / landing page
  pages/1_market_overview.py      → §1
  pages/2_credit_ratings.py       → §2
  pages/5_spreads_risk.py         → §5
"""

import streamlit as st

st.set_page_config(
    page_title="US Credit Risk Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Global CSS ────────────────────────────────────────────────
st.markdown(
    """
<style>
  /* ── Main content ── */
  .block-container { padding-top: 1.5rem; padding-bottom: 2rem; }
  hr { border: none; border-top: 0.5px solid #e0dfd8; margin: 1.5rem 0; }
  .chart-caption { font-size: 11px; color: #888780; margin-top: 4px; }
  .src-badge {
    display: inline-block; font-size: 10px; font-weight: 600;
    padding: 2px 8px; border-radius: 99px; margin-right: 4px;
  }
  .src-fred   { background: #E6F1FB; color: #0C447C; }
  .src-sifma  { background: #EAF3DE; color: #27500A; }
  .src-static { background: #FAEEDA; color: #633806; }

  /* ── Metric cards ── */
  [data-testid="metric-container"] {
    background: #f8f8f6; border: 0.5px solid #e0dfd8;
    border-radius: 10px; padding: 14px 18px;
  }
  [data-testid="metric-container"] label { font-size: 12px !important; color: #73726c; }
  [data-testid="metric-container"] [data-testid="stMetricValue"] { font-size: 22px !important; }

  /* ── Sidebar background ── */
  [data-testid="stSidebar"] { background: #1a1f2e !important; }
  [data-testid="stSidebar"] > div:first-child { padding-top: 0 !important; }

  /* ── Dashboard title injected above nav via ::before ── */
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

  /* ── Nav container ── */
  [data-testid="stSidebarNav"] { padding-top: 0 !important; }

  /* ── Nav links ── */
  [data-testid="stSidebarNavLink"] {
    border-radius: 8px !important;
    margin: 2px 8px !important;
    padding: 10px 14px !important;
    color: #9ba3b8 !important;
    font-size: 13px !important;
    font-weight: 400 !important;
    transition: background 0.15s, color 0.15s !important;
  }
  [data-testid="stSidebarNavLink"]:hover {
    background: rgba(255,255,255,0.07) !important;
    color: #e8eaf0 !important;
  }
  [data-testid="stSidebarNavLink"][aria-current="page"] {
    background: rgba(99,130,235,0.18) !important;
    color: #a5b4fc !important;
    font-weight: 500 !important;
  }
  [data-testid="stSidebarNavLink"] span { color: inherit !important; }

  /* ── Sidebar user-content area (below nav) ── */
  [data-testid="stSidebar"] section[data-testid="stSidebarUserContent"] {
    padding-top: 8px;
    border-top: 1px solid rgba(255,255,255,0.07);
  }
  [data-testid="stSidebar"] .stMarkdown p {
    color: #4a5278 !important;
    font-size: 11px !important;
    line-height: 1.6 !important;
  }
</style>
""",
    unsafe_allow_html=True,
)

# ── Sidebar footer (appears below nav — this is the only reliable position) ──
with st.sidebar:
    st.markdown(
        "FRED · SIFMA · S&P Global  \nAuto-updated daily via GitHub Actions",
    )

# ── Home page ─────────────────────────────────────────────────
st.title("US Corporate Credit Risk Dashboard")
st.markdown(
    "A live risk monitoring dashboard for the US public corporate bond market — "
    "investment grade (IG) and high yield (HY). "
    "Data ingested daily from FRED, updated quarterly from SIFMA."
)
st.markdown("---")

col1, col2, col3 = st.columns(3)
with col1:
    st.markdown(
        "**§1 Market overview**\n\nGlobal FI context, US market structure, corporate bond size & issuance."
    )
with col2:
    st.markdown(
        "**§2 Corporate bond & credit ratings**\n\nIG/HY intro, rating system, OAS by rating, default rates."
    )
with col3:
    st.markdown(
        "**§5 Spreads & risk** *(coming soon)*\n\nOAS history, z-score, volatility, spread vs default overlay."
    )

st.markdown("---")
st.markdown(
    '<p style="font-size:11px;color:#888">Data: FRED API · SIFMA · S&P Global Ratings · '
    "Auto-updated daily via GitHub Actions</p>",
    unsafe_allow_html=True,
)
