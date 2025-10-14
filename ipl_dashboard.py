import sys
import os
import pandas as pd
import plotly.express as px
import streamlit as st

# ---------------------------
# App Configuration
# ---------------------------
st.set_page_config(page_title="🏏 IPL Dashboard", layout="wide", page_icon="🏏")
st.title("🏏 IPL Data Analysis Dashboard")

# ---------------------------
# Load Data
# ---------------------------
def load_data(path="matches.csv"):
    """Load IPL match data or show an error if missing."""
    if not os.path.exists(path):
        st.error("⚠️ File 'matches.csv' not found. Please upload it to this folder.")
        st.stop()
    return pd.read_csv(path)

matches = load_data()

# ---------------------------
# Dashboard Sections
# ---------------------------

# 🥇 Top Winning Teams
st.subheader("🥇 Top Winning Teams")
team_wins = matches['winner'].dropna().value_counts().reset_index()
team_wins.columns = ['Team', 'Wins']
fig1 = px.bar(
    team_wins.head(10),
    x='Team',
    y='Wins',
    color='Team',
    title='Top 10 Teams by Wins',
    text='Wins'
)
fig1.update_traces(textposition='outside')
st.plotly_chart(fig1, use_container_width=True)

# 📈 Matches per Season
st.subheader("📈 Matches per Season")
season_matches = matches['season'].value_counts().sort_index().reset_index()
season_matches.columns = ['Season', 'Matches']
fig2 = px.line(
    season_matches,
    x='Season',
    y='Matches',
    markers=True,
    title='Matches per Season',
)
st.plotly_chart(fig2, use_container_width=True)

# 🏟️ Top Venues
st.subheader("🏟️ Top Venues by Matches Hosted")
venue_counts = matches['venue'].value_counts().head(10).reset_index()
venue_counts.columns = ['Venue', 'Matches']
fig3 = px.bar(
    venue_counts,
    x='Venue',
    y='Matches',
    color='Venue',
    title='Top 10 Venues by Matches Hosted',
    text='Matches'
)
fig3.update_traces(textposition='outside')
st.plotly_chart(fig3, use_container_width=True)

# 1️⃣ Top 5 Teams by Wins
# ---------------------------
st.subheader("🥇 Top 5 Teams by Wins")
team_wins = matches['winner'].dropna().value_counts().reset_index().head(5)
team_wins.columns = ['Team', 'Wins']
fig1 = px.bar(team_wins, x='Team', y='Wins', color='Team', text='Wins',
              title='Top 5 Teams by Wins')
fig1.update_traces(textposition='outside')
st.plotly_chart(fig1, use_container_width=True)
