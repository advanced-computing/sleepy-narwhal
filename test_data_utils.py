import pandas as pd

from data_utils import clean_inmate_race_data, filter_data_by_category


def test_filter_data_by_category():

    fake_data = pd.DataFrame({"Name": ["Alice", "Bob", "Charlie"], "Category": ["A", "B", "A"]})

    result_df = filter_data_by_category(fake_data, "Category", "A")

    assert len(result_df) == 2
    assert "Bob" not in result_df["Name"].values


def test_clean_inmate_race_data():

    raw_data = pd.DataFrame({"race": ["B", "W", None, "UNKNOWN", "OTHER"]})
    cleaned_df = clean_inmate_race_data(raw_data)
    result_list = cleaned_df["race"].tolist()
    expected_list = ["Black", "White", "Unknown", "Unknown", "Other"]

    assert result_list == expected_list
