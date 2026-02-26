import streamlit as st
import pandas as pd
import plotly.express as px
from data_utils import find_col, clean_date, filter_by_date, count_by_category, count_over_time

# Page config

st.set_page_config(page_title="NYC Inmates Dashboard", layout="wide")

st.title("NYC Daily Inmates in Custody Dashboard")
st.caption("Sleep-Narwhal | Team: Jing Bu, Gina Wang")

# Load data

@st.cache_data
def load_data():
    url = "https://data.cityofnewyork.us/api/views/7479-ugqb/rows.csv?accessType=DOWNLOAD"
    df = pd.read_csv(url)
    df.columns = df.columns.str.strip().str.lower()
    return df

df = load_data()

# Auto-detect important columns
date_col = find_col(df, "admitted_dt")
custody_col = find_col(df, "custody")
gender_col = find_col(df, "gender")
age_col = find_col(df, "age")
mh_col = find_col(df, "mental")

if date_col is None:
    st.error("No date column found.")
    st.write(df.columns)
    st.stop()

# Convert date
df = clean_date(df, date_col)

# Sidebar filters
st.sidebar.header("Filters")

start_date = df[date_col].min().date()
end_date = df[date_col].max().date()

date_range = st.sidebar.date_input(
    "Date Range",
    value=(start_date, end_date),
    min_value=start_date,
    max_value=end_date
)

df_filtered = filter_by_date(df, date_col, date_range[0], date_range[1])

# Metrics
col1, col2 = st.columns(2)
col1.metric("Total Rows (Filtered)", f"{len(df_filtered):,}")
col2.metric("Date Range", f"{date_range[0]} → {date_range[1]}")

st.divider()

# Visualization 1: Total inmates over time
st.subheader("Total Inmates Over Time")

df_time = count_over_time(df_filtered, date_col, freq="D")

fig1 = px.line(
    df_time,
    x=date_col,
    y="count",
    labels={date_col: "Date", "count": "Inmate Count"}
)

st.plotly_chart(fig1, use_container_width=True)


# Visualization 2: Custody Level Distribution

if custody_col:
    st.subheader("Custody Level Distribution")

    df_custody = count_by_category(df_filtered, custody_col)

    fig2 = px.bar(
        df_custody,
        x=custody_col,
        y="count",
        labels={custody_col: "Custody Level", "count": "Count"}
    )

    st.plotly_chart(fig2, use_container_width=True)

# Visualization 3: Gender Distribution

if gender_col:
    st.subheader("Gender Distribution")

    df_gender = count_by_category(df_filtered, gender_col)

    fig3 = px.pie(
        df_gender,
        names=gender_col,
        values="count"
    )

    st.plotly_chart(fig3, use_container_width=True)


# Visualization 4: Age Distribution

if age_col:
    st.subheader("Age Distribution")

    fig4 = px.histogram(
        df_filtered,
        x=age_col,
        nbins=20
    )

    st.plotly_chart(fig4, use_container_width=True)


# Visualization 5: Mental Health (if available)

if mh_col:
    st.subheader("Mental Health Observation Status")

    df_mh = count_by_category(df_filtered, mh_col)

    fig5 = px.bar(
        df_mh,
        x=mh_col,
        y="count"
    )

    st.plotly_chart(fig5, use_container_width=True)


# Data preview

with st.expander("Preview Data"):
    st.dataframe(df_filtered.head(100))
