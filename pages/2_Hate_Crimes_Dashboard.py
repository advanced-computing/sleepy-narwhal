import time

import pandas as pd
import plotly.express as px
import streamlit as st
from google.oauth2 import service_account

start_time = time.time()
st.set_page_config(page_title="Hate Crimes Dashboard", layout="wide")

st.header("📈 Part 2: NYPD Hate Crimes Analysis")


@st.cache_data(ttl=600)
def load_hate_crimes_motives():
    key_dict = st.secrets["gcp_service_account"]
    credentials = service_account.Credentials.from_service_account_info(key_dict)
    project_id = key_dict["project_id"]
    query = f"""
    SELECT bias_motive_description, COUNT(*) as count
    FROM `{project_id}.nyc_data.hate_crimes`
    GROUP BY bias_motive_description
    ORDER BY count DESC
    LIMIT 10
    """
    return pd.read_gbq(query, project_id=project_id, credentials=credentials)


@st.cache_data(ttl=600)
def load_hate_crimes_trends():
    key_dict = st.secrets["gcp_service_account"]
    credentials = service_account.Credentials.from_service_account_info(key_dict)
    project_id = key_dict["project_id"]
    query = f"""
    SELECT complaint_year_number, COUNT(*) as counts
    FROM `{project_id}.nyc_data.hate_crimes`
    WHERE complaint_year_number IS NOT NULL
    GROUP BY complaint_year_number
    ORDER BY complaint_year_number
    """
    return pd.read_gbq(query, project_id=project_id, credentials=credentials)


with st.spinner("Fetching aggregated Hate Crime data..."):
    df_motives = load_hate_crimes_motives()
    df_trends = load_hate_crimes_trends()

if not df_motives.empty and not df_trends.empty:
    # 【注意】因为我们没有下载全部原始数据，这里改为展示“统计后的前 10 动机数据”
    with st.expander("Click to view aggregated Hate Crimes data (Top Motives)"):
        st.dataframe(df_motives)

    # ==========================================
    # Chart A: Bias Motive
    # ==========================================
    st.subheader("What drives Hate Crimes? (Bias Motive)")

    # 现在的 df_motives 里面只有 10 行数据，且已经排好序了，直接画图！
    fig_bias = px.bar(
        df_motives,
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

    # ==========================================
    # Chart B: Trends
    # ==========================================
    st.subheader("Hate Crimes Trends over Years")

    # 把年份转成字符串，防止折线图的 X 轴出现 2,020.5 这种奇怪的带小数年份
    df_trends["complaint_year_number"] = df_trends["complaint_year_number"].astype(str)

    # 现在的 df_trends 里就是年份和总数，直接画图！
    fig_trend = px.line(
        df_trends,
        x="complaint_year_number",
        y="counts",
        markers=True,
        title="Total Hate Crimes per Year",
    )
    st.plotly_chart(fig_trend, use_container_width=True)

else:
    st.error("Failed to load Hate Crimes data.")

elapsed = time.time() - start_time
st.caption(f"⏱️ Page loaded in {elapsed:.2f} seconds")
