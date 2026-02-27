import pandas as pd


def filter_data_by_category(df, column_name, target_value):
    filtered_df = df[df[column_name] == target_value]
    return filtered_df


def clean_inmate_race_data(df):
    race_mapping = {
        "BLACK": "Black",
        "WHITE": "White",
        "HISPANIC": "Hispanic",
        "ASIAN": "Asian",
        "OTHER": "Other",
        "UNKNOWN": "Unknown",
        "B": "Black",
        "W": "White",
        "H": "Hispanic",
        "A": "Asian",
        "I": "American Indian",
        "O": "Other",
    }

    df_cleaned = df.copy()

    if "race" in df_cleaned.columns:
        df_cleaned["race"] = df_cleaned["race"].fillna("Unknown")
        df_cleaned["race"] = df_cleaned["race"].replace(race_mapping)

    return df_cleaned

    import pandera as pa


def validate_df(df, schema, df_name="dataframe"):
    try:
        return schema.validate(df, lazy=True)
    except pa.errors.SchemaErrors as e:
        raise ValueError(f"{df_name} schema validation failed:\n{e.failure_cases}") from e

