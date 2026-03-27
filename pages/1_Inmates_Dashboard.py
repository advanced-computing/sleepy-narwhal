import time

import pandas as pd
import plotly.express as px
import streamlit as st
from google.oauth2 import service_account

from data_utils import clean_inmate_race_data, filter_data_by_category

start_time = time.time()
st.set_page_config(page_title="Inmates Dashboard", layout="wide")

st.header("📊 Part 1: Daily Inmates In Custody")


@st.cache_data(ttl=600)
def load_inmate_data():
    try:
        key_dict = st.secrets["gcp_service_account"]
        credentials = service_account.Credentials.from_service_account_info(key_dict)
        project_id = key_dict["project_id"]

        # 只提取需要的 3 列
        query = f"SELECT race, custody_level, age FROM `{project_id}.nyc_data.daily_inmates`"
        df = pd.read_gbq(query, project_id=project_id, credentials=credentials)
        return df
    except Exception as e:
        st.error(f"Fail to fetch Inmate data from BigQuery: {e}")
        return pd.DataFrame()


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

elapsed = time.time() - start_time
st.caption(f"⏱️ Page loaded in {elapsed:.2f} seconds")
