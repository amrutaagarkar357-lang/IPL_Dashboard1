import streamlit as st
import pandas as pd
import plotly.express as px

# -------------------
# Load Data
# -------------------
@st.cache_data
def load_data():
    matches = pd.read_csv("https://raw.githubusercontent.com/<username>/<repo>/main/matches.csv")
    deliveries = pd.read_csv("https://raw.githubusercontent.com/<username>/<repo>/main/deliveries.csv")
    return matches, deliveries

matches, deliveries = load_data()

# -------------------
# Sidebar Filters
# -------------------
st.sidebar.header("Filters")
teams = matches["team1"].dropna().unique()   # dropna in case of blanks
selected_team = st.sidebar.selectbox("Select Team", sorted(teams))

# -------------------
# Runs Distribution
# -------------------
st.header("Runs Distribution")

team_deliveries = deliveries[deliveries["batting_team"] == selected_team]

total_runs = (
    team_deliveries.groupby("batsman")["batsman_runs"]
    .sum()
    .sort_values(ascending=False)
    .head(10)
)

df_runs = pd.DataFrame({
    "Batsman": total_runs.index,
    "Total Runs": total_runs.values
})

fig = px.bar(
    df_runs,
    x="Batsman",
    y="Total Runs",
    title=f"Top 10 Batsmen Runs for {selected_team}",
    text="Total Runs"
)
fig.update_traces(textposition="outside")
st.plotly_chart(fig)

# -------------------
# Top Bowlers
# -------------------
st.header("Top Bowlers")

team_bowling = deliveries[deliveries["bowling_team"] == selected_team]
total_wkts = (
    team_bowling[team_bowling["is_wicket"] == 1]
    .groupby("bowler")["is_wicket"]
    .count()
    .sort_values(ascending=False)
    .head(10)
)

df_wkts = pd.DataFrame({
    "Bowler": total_wkts.index,
    "Wickets": total_wkts.values
})

fig2 = px.bar(
    df_wkts,
    x="Bowler",
    y="Wickets",
    title=f"Top 10 Bowlers for {selected_team}",
    text="Wickets",
    color="Wickets"
)
fig2.update_traces(textposition="outside")
st.plotly_chart(fig2)

# -------------------
# Match Winning Trends
# -------------------
st.header("Winning Trends")

team_matches = matches[matches["winner"] == selected_team]
wins_per_season = team_matches.groupby("season")["id"].count()

df_wins = pd.DataFrame({
    "Season": wins_per_season.index,
    "Wins": wins_per_season.values
})

fig3 = px.line(
    df_wins,
    x="Season",
    y="Wins",
    title=f"Winning Trend per Season - {selected_team}",
    markers=True
)
st.plotly_chart(fig3)

# -------------------
# Stadium Trends
# -------------------
st.header("Stadium Trends")

venue_wins = (
    team_matches.groupby("venue")["id"]
    .count()
    .sort_values(ascending=False)
    .head(10)
)

df_venue = pd.DataFrame({
    "Stadium": venue_wins.index,
    "Wins": venue_wins.values
})

fig4 = px.bar(
    df_venue,
    x="Stadium",
    y="Wins",
    title=f"Top Stadiums where {selected_team} Won",
    text="Wins",
    color="Wins"
)
fig4.update_traces(textposition="outside")
st.plotly_chart(fig4)

st.success("Dashboard Loaded Successfully ✅")
