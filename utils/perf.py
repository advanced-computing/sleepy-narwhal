"""
utils/perf.py
=============
Performance helpers for the US Credit Risk Dashboard.

Two tools:
  display_load_time()  — context manager that shows elapsed page load time
                         (required by Lab 10 spec)
  profile_page()       — cProfile-based profiler for diagnosing slow pages
                         Toggle via sidebar checkbox; leave OFF in production.

Usage
-----
    from utils.perf import display_load_time, profile_page

    # Required: wrap all page content
    with display_load_time():
        st.markdown("## My page")
        df = load_data()
        st.plotly_chart(...)

    # Optional: add profiling during development
    with profile_page(top_n=20):
        ...page code...
"""

import cProfile
import io
import pstats
import time
from contextlib import contextmanager

import streamlit as st

# ── Required context manager (Lab 10 spec) ────────────────────


@contextmanager
def display_load_time():
    """
    Measures wall-clock time for a page render and displays it
    as a Streamlit caption at the bottom of the page.

    Usage:
        with display_load_time():
            # all page content here
    """
    start_time = time.time()
    try:
        yield
    finally:
        elapsed = time.time() - start_time
        st.caption(f"Page loaded in {elapsed:.2f}s")


# ── Optional profiling helper ─────────────────────────────────


@contextmanager
def profile_page(top_n: int = 20, sort_by: str = "cumulative"):
    """
    Context manager that runs cProfile on the wrapped code and
    renders a collapsible profiling report in the Streamlit page.

    Note: cProfile adds ~5-15% overhead. Disable in production.

    Args:
        top_n:   Number of functions to show in the report (default 20).
        sort_by: cProfile sort key — "cumulative" (total time including
                 callees, best for finding slow paths) or "tottime"
                 (time in function only, best for finding hot loops).

    How to read the output
    ----------------------
    Each row is one Python function. Key columns:

      ncalls     — how many times the function was called
      tottime    — seconds spent *inside* this function (excludes callees)
      cumtime    — seconds spent here *plus* all functions it called
      percall    — cumtime / ncalls (average time per call)
      filename   — source file and line number

    Look for:
      • High cumtime at the top  → slow code path (often I/O or BQ query)
      • High ncalls + low tottime → hot loop, consider vectorising
      • BQ client calls          → network round-trips, reduce with SQL pushdown
      • pandas operations        → groupby/pivot on large frames can be slow
    """
    pr = cProfile.Profile()
    pr.enable()
    try:
        yield
    finally:
        pr.disable()

        buf = io.StringIO()
        ps = pstats.Stats(pr, stream=buf)
        ps.strip_dirs()
        ps.sort_stats(sort_by)
        ps.print_stats(top_n)
        report = buf.getvalue()

        with st.expander(f"Profiling report — top {top_n} by {sort_by}", expanded=False):
            st.markdown("""
**How to read this:**
- **cumtime** — total time in this function *including* callees. High here = slow path.
- **tottime** — time *only inside* this function. High here = hot loop.
- **ncalls** — call count. Unexpectedly high = repeated work; consider caching.
- Lines mentioning `bigquery` or `http` = network I/O — reduce with SQL pushdown.
""")
            st.code(report, language="text")
