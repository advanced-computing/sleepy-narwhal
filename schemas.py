from pandera import Check, Column, DataFrameSchema

INMATES_SCHEMA = DataFrameSchema(
    {
        "race": Column(str, nullable=True),
        "custody_level": Column(str, nullable=True),
    },
    coerce=True,
    strict=False,
)

HATE_CRIMES_SCHEMA = DataFrameSchema(
    {
        "complaint_year_number": Column(
            int,
            nullable=True,
            checks=Check.in_range(1900, 2100),
        ),
        "bias_motive_description": Column(str, nullable=True),
    },
    coerce=True,
    strict=False,
)
