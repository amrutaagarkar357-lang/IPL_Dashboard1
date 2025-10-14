# IPL Dashboard using Streamlit + Matplotlib
# Automatically creates folders if missing
# Requires: matches.csv and deliveries.csv inside 'data/' folder

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os
from pathlib import Path

# --- Basic setup ---
st.set_page_config(page_title="IPL Dashboard (Matplotlib)", layout="wide")

# --- Step 1: Create folders automatically ---



# --- Step 2: File paths ---


# --- Step 3: Load dataset ---
@st.cache_data
def load_data():
    matches = pd.read_csv(MATCHES_PATH)
    deliveries = pd.read_csv(DELIVERIES_PATH)
    return matches, deliveries

try:
    matches, deliveries = load_data()
except FileNotFoundError:
    st.error("❌ Dataset not found! Please put 'matches.csv' and 'deliveries.csv' inside the 'data' folder.")
    st.stop()

# --- Sidebar Filters ---
st.sidebar.header("Filters")
seasons = sorted(matches['season'].dropna().unique())
selected_seasons = st.sidebar.multiselect("Select Season(s)", seasons, default=seasons[-3:])
teams = sorted(pd.unique(matches[['team1', 'team2']].values.ravel('K')))
selected_team = st.sidebar.selectbox("Select Team (or All)", ["All"] + teams)

# --- Filter data ---
f_matches = matches[matches['season'].isin(selected_seasons)]
match_ids = f_matches['id'].unique()
f_deliveries = deliveries[deliveries['match_id'].isin(match_ids)]

if selected_team != "All":
    f_matches = f_matches[(f_matches['team1'] == selected_team) | (f_matches['team2'] == selected_team)]
    match_ids = f_matches['id'].unique()
    f_deliveries = f_deliveries[f_deliveries['match_id'].isin(match_ids)]

# --- KPIs ---
total_matches = f_matches.shape[0]
total_runs = f_deliveries['total_runs'].sum()
total_wickets = f_deliveries[f_deliveries['dismissal_kind'].notna()].shape[0]
unique_players = pd.unique(pd.concat([f_deliveries['batsman'], f_deliveries['bowler']])).size

col1, col2, col3, col4 = st.columns(4)
col1.metric("Matches", total_matches)
col2.metric("Total Runs", int(total_runs))
col3.metric("Total Wickets", int(total_wickets))
col4.metric("Unique Players", int(unique_players))

st.markdown("---")

# --- 1️⃣ Matches per Season ---
st.subheader("Matches per Season")
matches_per_season = matches[matches['season'].isin(selected_seasons)].groupby('season').size()
fig1, ax1 = plt.subplots()
ax1.bar(matches_per_season.index, matches_per_season.values, color='royalblue')
ax1.set_xlabel("Season")
ax1.set_ylabel("Matches")
ax1.set_title("Matches per Season")
st.pyplot(fig1)

# --- 2️⃣ Runs per Over ---
st.subheader("Runs per Over")
runs_per_over = f_deliveries.groupby('over')['total_runs'].sum()
fig2, ax2 = plt.subplots()
ax2.plot(runs_per_over.index, runs_per_over.values, marker='o', color='green')
ax2.set_xlabel("Over")
ax2.set_ylabel("Runs")
ax2.set_title("Runs by Over")
st.pyplot(fig2)

# --- 3️⃣ Top 10 Batsmen ---
st.subheader("Top 10 Batsmen (by Runs)")
batsman_runs = f_deliveries.groupby('batsman')['batsman_runs'].sum().sort_values(ascending=False).head(10)
fig3, ax3 = plt.subplots()
ax3.barh(batsman_runs.index[::-1], batsman_runs.values[::-1], color='orange')
ax3.set_xlabel("Runs")
ax3.set_ylabel("Batsman")
ax3.set_title("Top 10 Batsmen")
st.pyplot(fig3)

# --- 4️⃣ Top 10 Bowlers ---
st.subheader("Top 10 Bowlers (by Wickets)")
wickets = f_deliveries[f_deliveries['dismissal_kind'].notna()]
wickets = wickets[~wickets['dismissal_kind'].isin(['run out', 'retired hurt'])]
bowler_wickets = wickets.groupby('bowler').size().sort_values(ascending=False).head(10)
fig4, ax4 = plt.subplots()
ax4.barh(bowler_wickets.index[::-1], bowler_wickets.values[::-1], color='crimson')
ax4.set_xlabel("Wickets")
ax4.set_ylabel("Bowler")
ax4.set_title("Top 10 Bowlers")
st.pyplot(fig4)

# --- 5️⃣ Team Wins ---
st.subheader("Team Wins")
team_wins = f_matches.groupby('winner').size().sort_values(ascending=False)
fig5, ax5 = plt.subplots()
ax5.bar(team_wins.index, team_wins.values, color='purple')
ax5.set_xlabel("Team")
ax5.set_ylabel("Wins")
ax5.set_title("Wins by Team")
plt.xticks(rotation=90)
st.pyplot(fig5)

# --- 6️⃣ Venue Scoring ---
st.subheader("Top Venues by Total Runs")
venue_runs = f_deliveries.groupby('venue')['total_runs'].sum().sort_values(ascending=False).head(10)
fig6, ax6 = plt.subplots()
ax6.barh(venue_runs.index[::-1], venue_runs.values[::-1], color='teal')
ax6.set_xlabel("Total Runs")
ax6.set_ylabel("Venue")
ax6.set_title("Top Venues by Aggregate Runs")
st.pyplot(fig6)

st.markdown("---")
st.caption("Dashboard built with Streamlit + Matplotlib | Data source: Kaggle IPL Dataset (matches.csv & deliveries.csv)")
