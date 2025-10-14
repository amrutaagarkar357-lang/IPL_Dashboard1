"""
Simplified IPL Dashboard — works safely even if matplotlib is not installed.

If running on Streamlit Cloud or similar restricted environments where `matplotlib`
is unavailable, this version uses Plotly Express only.

Usage:
  1. Download `matches.csv` from Kaggle IPL dataset.
  2. Place it in the same folder as this script.
  3. Run: `streamlit run ipl_dashboard.py`
"""

import sys
import os
import pandas as pd
import plotly.express as px

# Try to import streamlit safely
try:
    import streamlit as st
except ModuleNotFoundError:
    print("Streamlit not installed. Please run: pip install streamlit pandas plotly")
    sys.exit(1)


def load_data(path="matches.csv"):
    if not os.path.exists(path):
        st.error("⚠️ 'matches.csv' not found. Please add it to this folder.")
        st.stop()
    return pd.read_csv(path)


st.set_page_config(page_title="Easy IPL Dashboard", layout="wide")
st.title("🏏IPL Dashboard ")

# Load dataset
matches = load_data()

# --- Top Winning Teams ---
st.subheader("Top Winning Teams")
team_wins = matches['winner'].dropna().value_counts().reset_index()
team_wins.columns = ['Team', 'Wins']
fig1 = px.bar(team_wins.head(10), x='Team', y='Wins', color='Team', title='Top 10 Teams by Wins')
st.plotly_chart(fig1, use_container_width=True)

# --- Matches per Season ---
st.subheader("Matches per Season")
season_matches = matches['season'].value_counts().sort_index().reset_index()
season_matches.columns = ['Season', 'Matches']
fig2 = px.line(season_matches, x='Season', y='Matches', markers=True, title='Matches per Season')
st.plotly_chart(fig2, use_container_width=True)

# --- Top Venues ---
st.subheader("Top Venues by Matches Hosted")
venue_counts = matches['venue'].value_counts().head(10).reset_index()
venue_counts.columns = ['Venue', 'Matches']
fig3 = px.bar(venue_counts, x='Venue', y='Matches', color='Venue', title='Top 10 Venues by Matches Hosted')
st.plotly_chart(fig3, use_container_width=True)

st.markdown('---')

