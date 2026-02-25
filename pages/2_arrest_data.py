import streamlit as st
import pandas as pd
import plotly.express as px

st.title("NYC Arrest Data Overview")

@st.cache_data
def load_arrest():
    df = pd.read_csv("pages/arrest_data.csv")
    return df



df = load_arrest()

df_group = df.groupby("arrest_date").size().reset_index(name="count")

fig = px.line(df_group, x="arrest_date", y="count")

st.plotly_chart(fig)
