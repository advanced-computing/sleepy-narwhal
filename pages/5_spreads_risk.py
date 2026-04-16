"""
pages/5_spreads_risk.py
========================
§5  Spreads & risk metrics — placeholder
"""

import streamlit as st

from utils.perf import display_load_time

st.markdown(
    """
<style>
  .block-container { padding-top: 1.5rem; padding-bottom: 2rem; }
  hr { border: none; border-top: 0.5px solid #e0dfd8; margin: 1.5rem 0; }
  .chart-caption { font-size: 11px; color: #888780; margin-top: 4px; }
  .src-badge { display: inline-block; font-size: 10px; font-weight: 600; padding: 2px 8px; border-radius: 99px; margin-right: 4px; }
  .src-fred   { background: #E6F1FB; color: #0C447C; }
  .src-sifma  { background: #EAF3DE; color: #27500A; }
  .src-static { background: #FAEEDA; color: #633806; }
  [data-testid="metric-container"] { background: #f8f8f6; border: 0.5px solid #e0dfd8; border-radius: 10px; padding: 14px 18px; }
  [data-testid="metric-container"] label { font-size: 12px !important; color: #73726c; }
  [data-testid="metric-container"] [data-testid="stMetricValue"] { font-size: 22px !important; }
  [data-testid="stSidebar"] { background: #1a1f2e !important; }
  [data-testid="stSidebar"] > div:first-child { padding-top: 0 !important; }
  [data-testid="stSidebarNav"]::before {
    content: "US Credit Risk Dashboard";
    display: block; padding: 22px 20px 16px;
    font-size: 15px; font-weight: 600; color: #e8eaf0;
    letter-spacing: -0.01em;
    border-bottom: 1px solid rgba(255,255,255,0.07); margin-bottom: 6px;
  }
  [data-testid="stSidebarNav"] { padding-top: 0 !important; }
  [data-testid="stSidebarNavLink"] {
    border-radius: 8px !important; margin: 2px 8px !important;
    padding: 10px 14px !important; color: #9ba3b8 !important;
    font-size: 13px !important; font-weight: 400 !important;
    transition: background 0.15s, color 0.15s !important;
  }
  [data-testid="stSidebarNavLink"]:hover { background: rgba(255,255,255,0.07) !important; color: #e8eaf0 !important; }
  [data-testid="stSidebarNavLink"][aria-current="page"] { background: rgba(99,130,235,0.18) !important; color: #a5b4fc !important; font-weight: 500 !important; }
  [data-testid="stSidebarNavLink"] span { color: inherit !important; }
  [data-testid="stSidebar"] section[data-testid="stSidebarUserContent"] {
    padding-top: 8px; border-top: 1px solid rgba(255,255,255,0.07);
  }
  [data-testid="stSidebar"] .stMarkdown p { color: #4a5278 !important; font-size: 11px !important; line-height: 1.6 !important; }
</style>
""",
    unsafe_allow_html=True,
)

_ctx = display_load_time()

with _ctx:
    st.markdown("## §5  Spreads & risk metrics")
    st.info("Coming soon — IG/HY OAS history, z-score, volatility, spread vs default rate overlay.")
