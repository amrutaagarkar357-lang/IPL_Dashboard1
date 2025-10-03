import pandas as pd
import streamlit as st
import plotly.express as px

# Load dataset
df = pd.read_csv("ipl_dataset.csv")

# Dashboard Title
st.set_page_config(page_title="IPL Dashboard", layout="wide")
st.title("🏏 IPL Dashboard")
st.markdown("### Interactive Analysis of IPL Batting & Bowling Stats")

# Sidebar Filters
st.sidebar.header("⚙ Filters")
teams = df['batting_team'].unique()
selected_team = st.sidebar.selectbox("Select Team", options=["All"] + list(teams))

if selected_team != "All":
    df = df[df['batting_team'] == selected_team]

# Main Statistics Section
col1, col2, col3 = st.columns(3)
col1.metric("Total Matches", df['match_id'].nunique())
col2.metric("Total Runs", int(df['total_runs'].sum()))
col3.metric("Total Wickets", int(df[df['is_wicket']==1].shape[0]))

st.markdown("---")

# Top Batsmen
st.subheader("🔥 Top 10 Batsmen by Runs")
batsmen_runs = df.groupby('batsman')['total_runs'].sum().sort_values(ascending=False).head(10).reset_index()
fig_batsmen = px.bar(
    batsmen_runs, x='batsman', y='total_runs',
    color='total_runs', text='total_runs',
    color_continuous_scale="Blues", title="Top 10 Batsmen"
)
st.plotly_chart(fig_batsmen, use_container_width=True)

# Top Bowlers
st.subheader("🎯 Top 10 Bowlers by Wickets")
bowlers_wickets = df[df['is_wicket']==1].groupby('bowler')['is_wicket'].count().sort_values(ascending=False).head(10).reset_index()
fig_bowlers = px.bar(
    bowlers_wickets, x='bowler', y='is_wicket',
    color='is_wicket', text='is_wicket',
    color_continuous_scale="Oranges", title="Top 10 Bowlers"
)
st.plotly_chart(fig_bowlers, use_container_width=True)

# Runs Distribution
st.subheader("📊 Runs Distribution")
fig_runs = px.histogram(
    df, x="total_runs", nbins=10, color="total_runs",
    color_continuous_scale="Greens", title="Runs Distribution per Ball"
)
st.plotly_chart(fig_runs, use_container_width=True)

# Dataset Preview
with st.expander("🔍 View Raw Dataset"):
    st.dataframe(df.head(20))
