import pandas as pd

def find_col(df: pd.DataFrame, keyword: str):
    keyword = keyword.lower()
    for col in df.columns:
        if keyword in col.lower():
            return col
    return None

def clean_date(df: pd.DataFrame, date_col: str):
    df = df.copy()
    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
    return df.dropna(subset=[date_col])

def filter_by_date(df: pd.DataFrame, date_col: str, start_date, end_date):
    start = pd.to_datetime(start_date)
    end = pd.to_datetime(end_date)
    return df[(df[date_col] >= start) & (df[date_col] <= end)]

def count_by_category(df: pd.DataFrame, col: str):
    return df.groupby(col).size().reset_index(name="count")

def count_over_time(df: pd.DataFrame, date_col: str, freq: str = "D"):
    return (
        df.groupby(pd.Grouper(key=date_col, freq=freq))
          .size()
          .reset_index(name="count")
    )

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
