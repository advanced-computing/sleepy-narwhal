import time

import pandas as pd
import plotly.express as px
import requests
import streamlit as st

from data_utils import clean_inmate_race_data, filter_data_by_category
from data_validation import hate_crimes_schema, inmates_schema

# --- page setting ---
st.set_page_config(page_title="NYC Public Safety Analysis", layout="wide")

st.title("NYC Public Safety: Inmates & Hate Crimes Analysis")
st.markdown("### Team Members: Jinen Wang, Jing Bu")
st.markdown("---")

# ==========================================
# PART 1: Daily Inmates
# ==========================================


@st.cache_data
def load_inmate_data():
    # data import
    url = "https://data.cityofnewyork.us/resource/7479-ugqb.json?$limit=2000"
    try:
        df = pd.read_json(url)
        df = inmates_schema.validate(df)
        return df
    except Exception as e:
        st.error(f"Error loading inmate data: {e}")
        return pd.DataFrame()


st.header("Part 1: Daily Inmates In Custody")
with st.spinner("Loading Inmate Data..."):
    df_inmates = load_inmate_data()

if not df_inmates.empty:
    df_inmates = clean_inmate_race_data(df_inmates)

    # validate
    try:
        df_inmates = validate_df(df_inmates, INMATES_SCHEMA, "inmates")
    except ValueError as e:
        st.error(str(e))
        st.stop()

    custody_map = {"MIN": "Minimum", "MED": "Medium", "MAX": "Maximum"}
    df_inmates["custody_level"] = df_inmates["custody_level"].replace(custody_map)

    # --- plot ---
    st.subheader("Inmate Distribution by Race & Custody Level")

    custody_options = ["All"] + list(df_inmates["custody_level"].unique())
    selected_custody = st.selectbox("Filter by Custody Level:", custody_options)

    if selected_custody != "All":
        plot_df = filter_data_by_category(df_inmates, "custody_level", selected_custody)
    else:
        plot_df = df_inmates

    fig_inmates = px.histogram(
        plot_df,
        x="race",
        color="custody_level",
        barmode="group",
        title="Inmates by Race and Custody Level",
        text_auto=True,
        labels={
            "race": "Race Category",
            "custody_level": "Security Level",
        },
    )

    # category_orders={"race": ["Black", "Hispanic", "White", "Asian", "Other", "Unknown"]}
    # fig_inmates.update_layout(xaxis={'categoryorder':'array',
    # 'categoryarray': category_orders['race']})

    st.plotly_chart(fig_inmates, use_container_width=True)
else:
    st.warning("Failed to load Inmate data.")

st.markdown("---")
st.markdown("---")

# ==========================================
# TRANSITION: Connection between Datasets
# ==========================================

st.info("""
While the Inmate dataset reveals the racial disparities within the correctional system,
the Hate Crimes dataset supplements this by visualizing the patterns of bias and victimization
in the community, together providing a comprehensive view of how race intersects with public
safety in NYC.
""")

st.markdown("---")
# ==========================================
# PART 2: NYPD Hate Crimes
# ==========================================


@st.cache_data
def load_hate_crimes_data():
    base_url = "https://data.cityofnewyork.us/resource/bqiq-cu78.json"
    all_records = []
    limit = 1000
    offset = 0

    progress_text = "Loading Hate Crimes data... Please wait."
    my_bar = st.progress(0, text=progress_text)

    while True:
        params = {"$limit": limit, "$offset": offset}
        try:
            response = requests.get(base_url, params=params)
            response.raise_for_status()
            data = response.json()

            if not data:
                break

            all_records.extend(data)
            offset += limit

            progress = min(offset / 4500, 1.0)
            my_bar.progress(progress, text=f"Loaded {len(all_records)} rows...")
            time.sleep(0.1)

        except Exception as e:
            st.error(f"Error fetching data: {e}")
            break

    my_bar.empty()
    df = pd.DataFrame(all_records)

    try:
        df = hate_crimes_schema.validate(df)
    except Exception as e:
        st.warning(f"Data validation warning for Hate Crimes: {e}")
    return df


st.header("Part 2: NYPD Hate Crimes Analysis")
st.markdown(
    "Dataset: [NYPD Hate Crimes](https://data.cityofnewyork.us/Public-Safety/NYPD-Hate-Crimes/bqiq-cu78)"
)

with st.spinner("Fetching all Hate Crime records..."):
    df_hate = load_hate_crimes_data()

if not df_hate.empty:
    # validate
    try:
        df_hate = validate_df(df_hate, HATE_CRIMES_SCHEMA, "hate_crimes")
    except ValueError as e:
        st.error(str(e))
        st.stop()

    with st.expander("Click to view raw Hate Crimes data"):
        st.dataframe(df_hate.head(100))
        st.write(f"Total Records Fetched: {len(df_hate)}")

    if "complaint_year_number" in df_hate.columns:
        df_hate["complaint_year_number"] = pd.to_numeric(
            df_hate["complaint_year_number"], errors="coerce"
        )
        df_hate = df_hate.sort_values("complaint_year_number")

    # Chart A: Bias Motive
    st.subheader("What drives Hate Crimes? (Bias Motive)")

    if "bias_motive_description" in df_hate.columns:
        top_motives = df_hate["bias_motive_description"].value_counts().nlargest(10).index
        df_top_motives = df_hate[df_hate["bias_motive_description"].isin(top_motives)]

        fig_bias = px.bar(
            df_top_motives["bias_motive_description"].value_counts().reset_index(),
            x="bias_motive_description",
            y="count",
            labels={
                "bias_motive_description": "Bias Motive",
                "count": "Number of Incidents",
            },
            title="Top 10 Bias Motives for Hate Crimes",
            color="count",
            color_continuous_scale="Reds",
        )
        st.plotly_chart(fig_bias, use_container_width=True)

    # Chart B: Trends
    st.subheader("Hate Crimes Trends over Years")
    crime_by_year = df_hate.groupby("complaint_year_number").size().reset_index(name="counts")

    fig_trend = px.line(
        crime_by_year,
        x="complaint_year_number",
        y="counts",
        markers=True,
        title="Total Hate Crimes per Year",
    )
    st.plotly_chart(fig_trend, use_container_width=True)

else:
    st.error("Failed to load Hate Crimes data.")
