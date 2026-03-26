# import time
import pandas as pd
import plotly.express as px

# import requests
import streamlit as st
from google.oauth2 import service_account

from data_utils import clean_inmate_race_data, filter_data_by_category
from data_validation import hate_crimes_schema, inmates_schema

# --- page setting ---
st.set_page_config(page_title="NYC Public Safety Analysis", layout="wide")

st.title("NYC Public Safety: Inmates & Hate Crimes Analysis")
st.markdown("### Group sleepy-narwhal: Jinen (Gina) Wang, Jing Bu")
st.markdown("---")

tab1, tab2 = st.tabs(["📝 Project Proposal & Updates", "📊 Data Dashboard"])

# ==========================================
# TAB 1: PROPOSAL & UPDATES
# ==========================================
with tab1:
    st.header("Part 1: Original Proposal (As Is)")

    st.markdown("""
    **1. What dataset are you going to use?**
    * **Dataset Name:** Daily Inmates In Custody
    * **Source:** NYC Open Data (Department of Correction)
    * **Link:** [https://data.cityofnewyork.us/Public-Safety/Daily-Inmates-In-Custody/7479-ugqb](https://data.cityofnewyork.us/Public-Safety/Daily-Inmates-In-Custody/7479-ugqb)

    **2. What are your research question(s)?**
    * **Option A (Focus on Demographics & Security):** How does the distribution of custody
                levels (Min, Med, Max) vary across different racial groups and age brackets
                 within the NYC inmate population? Specifically, is there a statistically
                significant correlation between an inmate's age and their assigned security
                risk level (age will be broken down into age groups as brackets)?
    * **Option B (Focus on Mental Health):** What is the prevalence of mental health observation
                 (BRADH flag) among the inmate population, and how does this overlap with the
                'Infraction' status? Are inmates under mental observation more likely to have
                 recorded infractions compared to the general population?

    **3. What's the link to your notebook?**
    * **Link:** [https://github.com/advanced-computing/sleepy-narwhal/blob/branch1/main.ipynb](https://github.com/advanced-computing/sleepy-narwhal/blob/branch1/main.ipynb)

    **4. What's your target visualization? Include a picture.**
    * **Description:** We plan to create an interactive Stacked Bar Chart (using Plotly) to
                visualize the relationship between Race and Custody Level. The x-axis will
                represent different racial groups, while the y-axis will show the count of
                inmates, color-coded by their Custody Level (Min, Med, Max). This will allow
                for a clear comparison of security classifications across demographics and this
                visualization allows both absolute comparison and proportional inter.
    * **Picture:**
    """)
    st.markdown("")

    st.markdown("""
    **5. What are your known unknowns? What challenges do you anticipate?**
    * **Data Snapshot vs. Trends:** The dataset provides a daily snapshot ("Daily Inmates In
                Custody"). It does not inherently show historical trends or how an individual's
                 status changes over time unless I implement a script to collect data daily,
                which is outside the scope of a static analysis.
    * **Missing or Categorical Ambiguity:** Columns like race or gender may have missing values
                 or "Unknown" categories which could skew the demographic analysis. The definition
                of specific codes (like specific INFRACTION types) is not detailed in the dataset,
                 limiting the depth of behavioral analysis.
    * **Causality vs. Correlation:** While there’s evidence that certain groups have higher custody
                levels, the data does not contain the detailed case files or legal history required
                to explain why this is the case. So we must be careful not to imply causation from
                simple correlations.
    """)

    st.markdown("---")

    st.header("Part 2: Revisiting the Proposal (Updates & Insights)")

    st.info("""
    **Adjustments Made:**
    1. **Addition of a Second Dataset:** We expanded our scope by incorporating the
            **NYPD Hate Crimes dataset**. The original proposal solely focused on
            the systemic side of public safety (inmates).
    2. **Refined Focus:** While we kept our Option A research question regarding inmate
             demographics, we broadened our narrative to contrast "systemic penalization"
             with "community victimization."

    **New Insights Discovered:**
    * **Stark Demographic Contrasts:** The data reveals compelling concrete numbers
             regarding race. In the DOC Inmate data, Black and Hispanic individuals
             disproportionately make up the vast majority of the custody population
             (often exceeding **85%** combined), especially within the Maximum custody
             levels.
    * **The Flip Side of Public Safety:** Conversely, the Hate Crimes data reveals
             different racial and ethnic dynamics in community victimization. For
             instance, specific minority groups (such as Jewish and Asian communities)
             frequently emerge as the top targets of bias motives (e.g., Anti-Semitic
             and Anti-Asian motives often account for hundreds of reported incidents
             annually).
    * **Conclusion:** Relying solely on the inmate dataset would give a skewed,
             one-sided view of race in NYC public safety. By combining both, we
             can observe that racial vulnerability manifests differently: certain
             groups are more vulnerable to systemic incarceration, while others are
             highly vulnerable to targeted societal hate crimes.
    """)


# ==========================================
# PART 1: Daily Inmates
# ==========================================

with tab2:
    st.header("Data Dashboard")

    @st.cache_data(ttl=600)
    def load_inmate_data():
        try:
            key_dict = st.secrets["gcp_service_account"]
            credentials = service_account.Credentials.from_service_account_info(key_dict)
            project_id = key_dict["project_id"]

            query = f"SELECT * FROM `{project_id}.nyc_data.daily_inmates`"

            df = pd.read_gbq(query, project_id=project_id, credentials=credentials)
            if "inmates_schema" in globals():
                df = inmates_schema.validate(df)
            return df
        except Exception as e:
            st.error(f"Fail to fetch Inmate data from BigQuery: {e}")
            return pd.DataFrame()

    st.header("Part 1: Daily Inmates In Custody")
    with st.spinner("Loading Inmate Data..."):
        df_inmates = load_inmate_data()

    if not df_inmates.empty:
        df_inmates = clean_inmate_race_data(df_inmates)

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

        # ==========================================
        # 新增图表 A: 年龄分布箱线图 (Age vs Custody Level)
        # ==========================================
        st.subheader("1b. Age Distribution by Custody Level (Option A)")
        st.markdown("Exploring if younger inmates are assigned higher security levels.")

        # 1. 数据清洗：确保年龄是数字格式，并去除缺失值
        if "age" in df_inmates.columns:
            df_inmates["age"] = pd.to_numeric(df_inmates["age"], errors="coerce")
            df_age = df_inmates.dropna(subset=["age", "custody_level"])

            # 2. 画箱线图 (Box Plot)
            # 使用 category_orders 让 X 轴按照安全等级从低到高排列
            fig_age = px.box(
                df_age,
                x="custody_level",
                y="age",
                color="custody_level",
                title="Age vs. Custody Level",
                labels={"custody_level": "Security Level", "age": "Inmate Age"},
                category_orders={"custody_level": ["Minimum", "Medium", "Maximum"]},
            )
            st.plotly_chart(fig_age, use_container_width=True)

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

    @st.cache_data(ttl=600)
    def load_hate_crimes_data():
        with st.spinner("Loading Hate Crimes data from BigQuery..."):
            try:
                key_dict = st.secrets["gcp_service_account"]
                credentials = service_account.Credentials.from_service_account_info(key_dict)
                project_id = key_dict["project_id"]

                query = f"SELECT * FROM `{project_id}.nyc_data.hate_crimes`"
                df = pd.read_gbq(query, project_id=project_id, credentials=credentials)

                try:
                    df = hate_crimes_schema.validate(df)
                except Exception as e:
                    st.warning(f"Data validation warning for Hate Crimes: {e}")
                return df
            except Exception as e:
                st.error(f"Fail to fetch data from BigQuery: {e}")
                return pd.DataFrame()

    st.header("Part 2: NYPD Hate Crimes Analysis")
    st.markdown(
        "Dataset: [NYPD Hate Crimes](https://data.cityofnewyork.us/Public-Safety/NYPD-Hate-Crimes/bqiq-cu78)"
    )

    with st.spinner("Fetching all Hate Crime records..."):
        df_hate = load_hate_crimes_data()

    if not df_hate.empty:
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
