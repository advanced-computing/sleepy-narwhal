"""
tests/test_data_utils.py
========================
Unit tests for the pure calculation functions in data_utils.py.
These tests do NOT require a BigQuery connection — they only exercise
local Python/pandas logic and can run in CI without GCP credentials.

Run locally:
    pytest tests/ -v
    pytest tests/ --cov=data_utils --cov-report=term-missing
"""

import numpy as np
import pandas as pd
import pytest

from data_utils import (
    compute_spread_percentile,
    compute_spread_zscore,
    regime_flag,
    yoy_change,
)

# ── Fixtures ──────────────────────────────────────────────────────────────


@pytest.fixture
def flat_spread():
    """A constant spread series — z-score should always be NaN or 0."""
    dates = pd.date_range("2020-01-01", periods=300, freq="B")
    return pd.Series(100.0, index=dates, name="oas")


@pytest.fixture
def trending_spread():
    """A spread that rises linearly from 100 to 599 over 500 business days."""
    dates = pd.date_range("2018-01-01", periods=500, freq="B")
    values = np.linspace(100, 599, 500)
    return pd.Series(values, index=dates, name="oas")


@pytest.fixture
def yoy_df():
    """DataFrame with a 'value' column and dates exactly 2 years apart."""
    return pd.DataFrame(
        {
            "date": pd.to_datetime(["2022-01-03", "2023-01-03", "2024-01-02"]),
            "value": [100.0, 110.0, 132.0],
        }
    )


# ── Test 1: compute_spread_zscore ─────────────────────────────────────────


class TestComputeSpreadZscore:
    """
    Z-score = (x - rolling_mean) / rolling_std.
    A constant series has std = 0, so values can't be standardised —
    the result should be NaN everywhere (division by zero).
    For a series with real variance, z-scores should be centred near 0
    and the most recent extreme value should have a large positive z-score.
    """

    def test_constant_series_returns_nan(self, flat_spread):
        result = compute_spread_zscore(flat_spread, window=252)
        # Constant series: std = 0 → all z-scores NaN
        assert result.dropna().empty, "Z-scores for a constant series should all be NaN (std = 0)"

    def test_output_length_matches_input(self, trending_spread):
        result = compute_spread_zscore(trending_spread, window=252)
        assert len(result) == len(trending_spread)

    def test_early_values_are_nan_before_window(self, trending_spread):
        window = 252
        result = compute_spread_zscore(trending_spread, window=window)
        # With min_periods = window // 2 = 126, the first 125 values are NaN
        assert result.iloc[: window // 2 - 1].isna().all(), "Values before min_periods should be NaN"

    def test_last_value_is_large_positive(self, trending_spread):
        result = compute_spread_zscore(trending_spread, window=252)
        last_z = result.dropna().iloc[-1]
        assert last_z > 1.0, f"Spread at its 500-day high should have a positive z-score, got {last_z:.2f}"


# ── Test 2: yoy_change ────────────────────────────────────────────────────


class TestYoyChange:
    """
    Year-over-year % change = (latest - prev_year) / |prev_year| * 100.
    Uses the last row and the most recent row whose date is ≥ 1 year before it.
    """

    def test_correct_percentage(self, yoy_df):
        # latest = 132 (2024-01-02), one year ago = 110 (2023-01-03)
        # YoY = (132 - 110) / 110 * 100 = 20.0
        result = yoy_change(yoy_df, "value")
        assert result == pytest.approx(20.0, abs=0.2), f"Expected ~20.0% YoY change, got {result}"

    def test_returns_nan_for_single_row(self):
        df = pd.DataFrame(
            {
                "date": pd.to_datetime(["2024-01-01"]),
                "value": [100.0],
            }
        )
        result = yoy_change(df, "value")
        assert np.isnan(result), "Single-row DataFrame should return NaN"

    def test_returns_nan_when_no_prior_year(self):
        # Only 6 months of data — no row far enough back for a YoY comparison
        df = pd.DataFrame(
            {
                "date": pd.date_range("2024-01-01", periods=3, freq="90D"),
                "value": [100.0, 105.0, 110.0],
            }
        )
        result = yoy_change(df, "value")
        assert np.isnan(result), "Should return NaN when there is no data point >= 1 year before latest"

    def test_positive_growth_is_positive(self, yoy_df):
        result = yoy_change(yoy_df, "value")
        assert result > 0

    def test_negative_growth_is_negative(self):
        df = pd.DataFrame(
            {
                "date": pd.to_datetime(["2023-01-03", "2024-01-02"]),
                "value": [200.0, 150.0],
            }
        )
        result = yoy_change(df, "value")
        assert result < 0, f"Expected negative YoY change, got {result}"


# ── Test 3: regime_flag ───────────────────────────────────────────────────


class TestRegimeFlag:
    """
    regime_flag(percentile) classifies the current spread level
    into four regimes and returns (label, color_hex).

    Boundaries:
      >= 75  → Wide — stressed   (#A32D2D, red)
      >= 50  → Above median      (#BA7517, amber)
      >= 25  → Below median      (#3B6D11, green)
      <  25  → Tight — rich      (#185FA5, blue)
    """

    @pytest.mark.parametrize(
        "percentile, expected_label, expected_color",
        [
            (90, "Wide — stressed", "#A32D2D"),
            (75, "Wide — stressed", "#A32D2D"),  # boundary: exactly 75
            (74.9, "Above median", "#BA7517"),
            (50, "Above median", "#BA7517"),  # boundary: exactly 50
            (49.9, "Below median", "#3B6D11"),
            (25, "Below median", "#3B6D11"),  # boundary: exactly 25
            (24.9, "Tight — rich", "#185FA5"),
            (0, "Tight — rich", "#185FA5"),
        ],
    )
    def test_all_boundaries(self, percentile, expected_label, expected_color):
        label, color = regime_flag(percentile)
        assert label == expected_label, f"percentile={percentile}: expected label '{expected_label}', got '{label}'"
        assert color == expected_color, f"percentile={percentile}: expected color '{expected_color}', got '{color}'"

    def test_returns_tuple_of_two_strings(self):
        result = regime_flag(50)
        assert isinstance(result, tuple) and len(result) == 2
        assert all(isinstance(x, str) for x in result)

    def test_color_is_valid_hex(self):
        for percentile in [0, 25, 50, 75, 100]:
            _, color = regime_flag(percentile)
            assert color.startswith("#") and len(color) == 7, f"Color '{color}' is not a valid 7-char hex string"
