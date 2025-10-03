import streamlit as st
import pandas as pd
import plotly.express as px

# ---------------------
# 1. Page Config
# ---------------------
st.set_page_config(page_title="IPL Dashboard", layout="wide")

st.markdown("<h1 style='text-align: center; color: #133D8D;'>🏏 IPL Dashboard</h1>", unsafe_allow_html=True)
st.markdown("<h4 style='text-align: center; color: #D71920;'>Official Style Dashboard (with Kaggle Data)</h4>", unsafe_allow_html=True)

# ---------------------
# 2. Load Data
# ---------------------
matches = pd.read_csv("matches.csv")
deliveries = pd.read_csv("deliveries.csv")

# ---------------------
# 3. Sidebar Filters
# ---------------------
st.sidebar.header("🔍 Filters")
season = st.sidebar.selectbox("Select Season", sorted(matches['season'].unique()))
season_matches = matches[matches['season'] == season]

# ---------------------
# 4. KPIs
# ---------------------
total_matches = season_matches.shape[0]
most_wins = season_matches['winner'].value_counts().idxmax()
top_stadium = season_matches['venue'].value_counts().idxmax()

col1, col2, col3 = st.columns(3)
col1.metric("🏆 Total Matches", total_matches)
col2.metric("🥇 Most Winning Team", most_wins)
col3.metric("🏟 Top Stadium", top_stadium)

# ---------------------
# 5. Top Scorers
# ---------------------
season_ids = season_matches['id'].unique()
season_deliveries = deliveries[deliveries['match_id'].isin(season_ids)]

top_scorers = season_deliveries.groupby('batsman')['batsman_runs'].sum().sort_values(ascending=False).head(10)
fig1 = px.bar(top_scorers, x=top_scorers.values, y=top_scorers.index,
              orientation='h', title=f"Top 10 Scorers in {season}",
              labels={"x": "Runs", "y": "Batsman"},
              color=top_scorers.values, color_continuous_scale="blues")

# ---------------------
# 6. Stadium Trends
# ---------------------
stadium_wins = season_matches['venue'].value_counts().head(10)
fig2 = px.bar(stadium_wins, x=stadium_wins.values, y=stadium_wins.index,
              orientation='h', title=f"Top Stadiums in {season}",
              labels={"x": "Matches", "y": "Stadium"},
              color=stadium_wins.values, color_continuous_scale="reds")

# ---------------------
# 7. Winning Teams Chart
# ---------------------
winning_teams = season_matches['winner'].value_counts()
fig3 = px.pie(winning_teams, names=winning_teams.index, values=winning_teams.values,
              title=f"Winning Teams Share in {season}",
              color_discrete_sequence=px.colors.qualitative.Safe)

# ---------------------
# 8. Layout
# ---------------------
st.plotly_chart(fig1, use_container_width=True)
st.plotly_chart(fig2, use_container_width=True)
st.plotly_chart(fig3, use_container_width=True)
