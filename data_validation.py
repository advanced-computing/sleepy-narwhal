import pandera as pa
from pandera import Check, Column

# ==========================================
# 1. Inmates
# ==========================================
inmates_schema = pa.DataFrameSchema(
    {
        "race": Column(str, nullable=True),
        "custody_level": Column(str, Check.isin(["MIN", "MED", "MAX"]), nullable=True),
    },
    ignore_unknown_columns=True,
)

# ==========================================
# 2. Hate Crimes
# ==========================================
hate_crimes_schema = pa.DataFrameSchema(
    {
        "complaint_year_number": Column(int, Check.ge(2019), nullable=True, coerce=True),
        "bias_motive_description": Column(str, nullable=True),
    },
    ignore_unknown_columns=True,
)
