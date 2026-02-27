import pandas as pd
import pytest

from schemas import INMATES_SCHEMA
from data_utils import validate_df


def test_inmates_schema_passes_minimal():
    df = pd.DataFrame(
        {
            "race": ["Black", "White"],
            "custody_level": ["Minimum", "Maximum"],
        }
    )
    out = validate_df(df, INMATES_SCHEMA, "inmates")
    assert len(out) == 2


def test_inmates_schema_fails_bad_year_column_not_required():
    df = pd.DataFrame(
        {"race": ["Black"], "custody_level": ["Minimum"], "extra": [123]}
    )
    out = validate_df(df, INMATES_SCHEMA, "inmates")
    assert "extra" in out.columns
