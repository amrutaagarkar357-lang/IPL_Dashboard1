import pandas as pd
import streamlit as st
import plotly.express as px

# Load dataset
df = pd.read_csv('ipl_dataset.csv')

# Dashboard title
st.title("IPL Dashboard")

# Show dataset
st.subheader("Dataset Preview")
st.dataframe(df.head())

# Total stats
st.subheader("Statistics")
st.metric("Total Matches", df['match_id'].nunique())
st.metric("Total Runs", df['total_runs'].sum())
st.metric("Total Wickets", df[df['is_wicket']==1].shape[0])

# Top Batsmen
st.subheader("Top 10 Batsmen")
batsmen = df.groupby('batsman')['total_runs'].sum().sort_values(ascending=False).head(10).reset_index()
st.bar_chart(batsmen.set_index('batsman'))

# Top Bowlers
st.subheader("Top 10 Bowlers")
bowlers = df[df['is_wicket']==1].groupby('bowler')['is_wicket'].count().sort_values(ascending=False).head(10).reset_index()
st.bar_chart(bowlers.set_index('bowler'))
