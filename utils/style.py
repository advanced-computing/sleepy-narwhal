"""
Shared styling and sidebar rendering for the credit dashboard.
"""

from __future__ import annotations

import streamlit as st

THEME_CSS = """
<style>
  :root {
    --sipa-blue: #003c7d;
    --sipa-sky: #eaf6ff;
    --ink: #101828;
    --muted: #536178;
    --line: #d8e4f2;
    --panel: #ffffff;
    --soft: #f6f9fd;
    --accent: #ff4d55;
    --green: #1f8a5b;
    --amber: #b96b19;
    --red: #a32d2d;
  }

  html, body, [class*="css"] {
    font-family: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
    color: var(--ink);
  }
  .stApp {
    background:
      radial-gradient(circle at 8% 0%, rgba(227, 244, 255, 0.78), transparent 30rem),
      linear-gradient(180deg, #fbfdff 0%, #f7faff 42%, #ffffff 100%);
  }
  .block-container {
    max-width: 1180px;
    padding-top: 2.1rem;
    padding-bottom: 2.4rem;
  }
  h1, h2, h3, h4 {
    color: #0b1328 !important;
    letter-spacing: 0 !important;
  }
  h2 {
    font-size: 2.25rem !important;
    line-height: 1.08 !important;
    font-weight: 750 !important;
    margin-bottom: 0.7rem !important;
  }
  h4 {
    font-size: 1rem !important;
    font-weight: 700 !important;
    margin-top: 1rem !important;
  }
  p {
    color: var(--muted) !important;
    font-size: 0.96rem !important;
    line-height: 1.65 !important;
  }
  hr {
    border: none;
    border-top: 1px solid var(--line);
    margin: 1rem 0;
  }

  /* Hide Streamlit's default multipage nav; we render our own module nav. */
  [data-testid="stSidebarNav"] { display: none !important; }
  [data-testid="stSidebar"] {
    background:
      radial-gradient(circle at 15% 4%, rgba(220, 242, 255, 0.92), transparent 16rem),
      linear-gradient(180deg, #f8fcff 0%, #ffffff 48%, #f8fbff 100%) !important;
    border-right: 1px solid var(--line) !important;
    box-shadow: 12px 0 34px rgba(16, 24, 40, 0.04);
  }
  [data-testid="stSidebar"] > div:first-child {
    padding: 0.95rem 1.2rem 1rem !important;
  }
  [data-testid="stSidebar"] section[data-testid="stSidebarUserContent"] {
    padding-top: 0 !important;
  }

  .sidebar-product-card {
    background: rgba(255, 255, 255, 0.82);
    border: 1px solid var(--line);
    border-radius: 1rem;
    padding: 0.92rem 1rem;
    box-shadow: 0 12px 26px rgba(23, 60, 99, 0.08);
    margin-bottom: 1.05rem;
  }
  .sidebar-eyebrow {
    color: #00659b;
    font-size: 0.68rem;
    font-weight: 800;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    margin-bottom: 0.62rem;
  }
  .sidebar-title {
    color: #0b1328;
    font-family: "SFMono-Regular", Consolas, "Liberation Mono", monospace;
    font-size: 1.08rem;
    font-weight: 800;
    letter-spacing: 0;
    line-height: 1.1;
    margin-bottom: 0.55rem;
  }
  .sidebar-copy {
    color: #536178;
    font-size: 0.78rem;
    line-height: 1.42;
  }
  .module-label {
    color: #697891;
    font-weight: 800;
    font-size: 0.7rem;
    letter-spacing: 0.16em;
    text-transform: uppercase;
    margin: 0 0 0.45rem;
  }
  [data-testid="stSidebar"] [data-testid="stPageLink"] {
    margin: 0 !important;
  }
  [data-testid="stSidebar"] [data-testid="stPageLink"] a {
    position: relative;
    display: flex;
    align-items: center;
    min-height: 1.78rem;
    padding: 0.22rem 0.25rem 0.22rem 1.82rem !important;
    border-radius: 0.75rem;
    color: #344258 !important;
    font-size: 0.82rem !important;
    font-weight: 720 !important;
    text-decoration: none !important;
  }
  [data-testid="stSidebar"] [data-testid="stPageLink"] a::before {
    content: "";
    position: absolute;
    left: 0.28rem;
    width: 0.86rem;
    height: 0.86rem;
    border-radius: 99px;
    border: 2px solid #d0d5dd;
    background: #fbfcff;
  }
  [data-testid="stSidebar"] [data-testid="stPageLink"] a:hover {
    background: rgba(0, 60, 125, 0.06) !important;
    color: #15243a !important;
  }
  [data-testid="stSidebar"] [data-testid="stPageLink"] a[aria-current="page"] {
    background: transparent !important;
    color: #26364d !important;
  }
  [data-testid="stSidebar"] [data-testid="stPageLink"] a[aria-current="page"]::before {
    border-color: var(--accent);
    background: radial-gradient(circle, #ffffff 0 28%, var(--accent) 31% 100%);
  }
  .sidebar-footnote {
    color: #8a96aa;
    font-size: 0.6rem;
    line-height: 1.35;
    margin-top: 0.72rem;
  }

  [data-testid="metric-container"] {
    background: rgba(255, 255, 255, 0.86);
    border: 1px solid var(--line);
    border-radius: 0.85rem;
    padding: 0.78rem 0.95rem;
    box-shadow: 0 12px 26px rgba(25, 52, 83, 0.06);
  }
  [data-testid="metric-container"] label {
    color: #718098 !important;
    font-size: 0.68rem !important;
    font-weight: 800 !important;
    letter-spacing: 0.08em;
    text-transform: uppercase;
  }
  [data-testid="metric-container"] [data-testid="stMetricValue"] {
    color: #0b1328 !important;
    font-size: 1.42rem !important;
    font-weight: 800 !important;
  }
  [data-testid="metric-container"] [data-testid="stMetricDelta"] {
    font-size: 0.72rem !important;
    font-weight: 700 !important;
  }

  .signal-card {
    background: rgba(255, 255, 255, 0.86);
    border: 1px solid var(--line);
    border-left: 4px solid var(--sipa-blue);
    border-radius: 0.95rem;
    padding: 1rem 1.1rem;
    margin: 0.45rem 0 0.8rem;
    box-shadow: 0 14px 30px rgba(25, 52, 83, 0.07);
  }
  .signal-label {
    font-size: 0.66rem;
    font-weight: 850;
    letter-spacing: 0.13em;
    text-transform: uppercase;
    margin-bottom: 0.32rem;
  }
  .signal-title {
    color: #0b1328;
    font-size: 1rem;
    line-height: 1.28;
    font-weight: 800;
    margin-bottom: 0.45rem;
  }
  .signal-body {
    color: var(--muted);
    font-size: 0.82rem;
    line-height: 1.55;
  }
  .tag-row { margin-top: 0.65rem; }
  .tag {
    display: inline-block;
    background: #f2f6fb;
    border: 1px solid #dde7f4;
    border-radius: 99px;
    padding: 0.18rem 0.48rem;
    margin: 0.12rem 0.14rem 0.12rem 0;
    color: #536178;
    font-size: 0.66rem;
    font-weight: 700;
  }
  .regime-badge {
    display: inline-block;
    padding: 0.22rem 0.72rem;
    border-radius: 99px;
    font-size: 0.72rem;
    font-weight: 800;
  }
  .chart-caption {
    color: #8a96aa !important;
    font-size: 0.68rem !important;
    margin-top: 0.15rem;
  }
  .src-badge {
    display: inline-block;
    border-radius: 99px;
    padding: 0.08rem 0.43rem;
    margin-right: 0.25rem;
    font-size: 0.58rem;
    font-weight: 850;
    letter-spacing: 0.04em;
  }
  .src-fred { background: #e8f2ff; color: #1d4ed8; }
  .src-sifma { background: #eaf7ef; color: #166534; }
  .src-static { background: #fff0ea; color: #b54708; }

  [data-testid="stPlotlyChart"] {
    background: rgba(255,255,255,0.68);
    border: 1px solid rgba(216, 228, 242, 0.75);
    border-radius: 0.95rem;
    padding: 0.3rem;
    box-shadow: 0 12px 28px rgba(25, 52, 83, 0.045);
  }
  [data-testid="stExpander"] {
    border: 1px solid var(--line) !important;
    border-radius: 0.9rem !important;
    background: rgba(255,255,255,0.82) !important;
  }
  [data-testid="stTabs"] button {
    font-size: 0.82rem !important;
    font-weight: 750 !important;
  }
  [data-testid="stSegmentedControl"] [role="group"],
  [data-testid="stSegmentedControl"] [role="radiogroup"],
  [data-testid="stRadio"] [role="radiogroup"] {
    flex-wrap: nowrap !important;
    white-space: nowrap !important;
  }
  [data-testid="stSegmentedControl"] button {
    min-width: 3.2rem !important;
    padding-left: 0.62rem !important;
    padding-right: 0.62rem !important;
  }
</style>
"""


PAGES = [
    ("Executive Briefing", "app.py"),
    ("Spread Regime", "pages/1_spread_regime.py"),
    ("Credit Curve", "pages/2_credit_curve.py"),
    ("Spread vs Macro", "pages/5_spreads_risk.py"),
    ("Strategy Outlook", "pages/6_strategy_outlook.py"),
]


def inject_css() -> None:
    """Inject the shared visual system."""
    st.markdown(THEME_CSS, unsafe_allow_html=True)


def render_sidebar() -> None:
    """Render the SIPA-inspired custom sidebar navigation."""
    with st.sidebar:
        st.markdown(
            """
            <div class="sidebar-product-card">
              <div class="sidebar-title">Credit Market Dashboard 📈</div>
            </div>
            <div class="module-label">Module</div>
            """,
            unsafe_allow_html=True,
        )
        for label, path in PAGES:
            st.page_link(path, label=label)
        st.markdown(
            """
            <div class="sidebar-footnote">FRED · SIFMA · S&P Global<br>Auto-updated daily at 06:00 UTC</div>
            """,
            unsafe_allow_html=True,
        )
