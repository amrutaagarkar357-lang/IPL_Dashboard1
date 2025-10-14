import sys
import os
import pandas as pd
import plotly.express as px
import streamlit as st

# ---------------------------
# Streamlit Config
# ---------------------------
st.set_page_config(page_title="🏏 IPL Dashboard", layout="wide", page_icon="🏏")
st.title("🏏 IPL Data Analysis Dashboard")

# ---------------------------
# Load Data
# ---------------------------
def load_data(matches_path="matches.csv", deliveries_path="deliveries.csv"):
    if not os.path.exists(matches_path) or not os.path.exists(deliveries_path):
        st.error("⚠️ Please add both 'matches.csv' and 'deliveries.csv' in this folder.")
        st.stop()
   import os
print("matches.csv exists:", os.path.exists("matches.csv"))
print("deliveries.csv exists:", os.path.exists("deliveries.csv"))

    return matches, deliveries

matches, deliveries = load_data()

# ---------------------------
# 1️⃣ Top 5 Teams by Wins
# ---------------------------
st.subheader("🥇 Top 5 Teams by Wins")
team_wins = matches['winner'].dropna().value_counts().reset_index().head(5)
team_wins.columns = ['Team', 'Wins']
fig1 = px.bar(team_wins, x='Team', y='Wins', color='Team', text='Wins',
              title='Top 5 Teams by Wins')
fig1.update_traces(textposition='outside')
st.plotly_chart(fig1, use_container_width=True)

# ---------------------------
# 2️⃣ Top 5 Batsmen by Total Runs
# ---------------------------
st.subheader("🏏 Top 5 Batsmen by Total Runs")
top_batsmen = deliveries.groupby('batsman')['batsman_runs'].sum().reset_index()
top_batsmen = top_batsmen.sort_values(by='batsman_runs', ascending=False).head(5)
fig2 = px.bar(top_batsmen, x='batsman', y='batsman_runs', color='batsman', text='batsman_runs',
              title='Top 5 Batsmen by Runs')
fig2.update_traces(textposition='outside')
st.plotly_chart(fig2, use_container_width=True)

# ---------------------------
# 3️⃣ Top 5 Bowlers by Wickets
# ---------------------------
st.subheader("🎯 Top 5 Bowlers by Wickets")
# count wickets (exclude 'run out', 'retired hurt', etc.)
valid_wickets = deliveries[deliveries['dismissal_kind'].isin(
    ['bowled', 'caught', 'lbw', 'stumped', 'caught and bowled', 'hit wicket']
)]
top_bowlers = valid_wickets['bowler'].value_counts().reset_index().head(5)
top_bowlers.columns = ['Bowler', 'Wickets']
fig3 = px.bar(top_bowlers, x='Bowler', y='Wickets', color='Bowler', text='Wickets',
              title='Top 5 Bowlers by Wickets')
fig3.update_traces(textposition='outside')
st.plotly_chart(fig3, use_container_width=True)

# ---------------------------
# 4️⃣ Top 5 Stadiums (Venues)
# ---------------------------
st.subheader("🏟️ Top 5 Stadiums by Matches Hosted")
top_stadiums = matches['venue'].value_counts().head(5).reset_index()
top_stadiums.columns = ['Stadium', 'Matches']
fig4 = px.bar(top_stadiums, x='Stadium', y='Matches', color='Stadium', text='Matches',
              title='Top 5 Stadiums by Matches Hosted')
fig4.update_traces(textposition='outside')
st.plotly_chart(fig4, use_container_width=True)
