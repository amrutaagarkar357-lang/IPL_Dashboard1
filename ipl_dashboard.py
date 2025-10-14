IPL_Streamlit_Dashboard.py

Streamlit dashboard for IPL analysis using Kaggle 'matches.csv' and 'deliveries.csv'

Place matches.csv and deliveries.csv in a folder named 'data' next to this file.

import streamlit as st import pandas as pd import plotly.express as px import plotly.graph_objects as go from pathlib import Path

st.set_page_config(page_title='IPL Dashboard', layout='wide', initial_sidebar_state='expanded')

DATA_DIR = Path('./data') MATCHES_PATH = DATA_DIR / 'matches.csv' DELIVERIES_PATH = DATA_DIR / 'deliveries.csv'

@st.cache_data def load_data(): matches = pd.read_csv(MATCHES_PATH) deliveries = pd.read_csv(DELIVERIES_PATH) return matches, deliveries

Load

try: matches, deliveries = load_data() except Exception as e: st.error(f"Could not load data from {DATA_DIR}. Make sure 'matches.csv' and 'deliveries.csv' exist.\nError: {e}") st.stop()

Sidebar filters

st.sidebar.title('Filters') seasons = sorted(matches['season'].dropna().unique()) selected_seasons = st.sidebar.multiselect('Season(s)', seasons, default=seasons[-3:]) teams = sorted(pd.unique(matches[['team1','team2']].values.ravel('K'))) selected_team = st.sidebar.selectbox('Team (All for overall)', ['All'] + teams)

Filtered datasets

f_matches = matches[matches['season'].isin(selected_seasons)] match_ids = f_matches['id'].unique() f_deliveries = deliveries[deliveries['match_id'].isin(match_ids)]

if selected_team != 'All': f_matches = f_matches[(f_matches['team1']==selected_team) | (f_matches['team2']==selected_team)] match_ids = f_matches['id'].unique() f_deliveries = deliveries[deliveries['match_id'].isin(match_ids)]

KPIs

total_matches = f_matches.shape[0] total_runs = f_deliveries['total_runs'].sum() total_wickets = f_deliveries[f_deliveries['dismissal_kind'].notna()].shape[0] unique_players = pd.unique(pd.concat([f_deliveries['batsman'], f_deliveries['bowler']])).size

col1, col2, col3, col4 = st.columns(4) col1.metric('Matches', total_matches) col2.metric('Runs (filtered)', int(total_runs)) col3.metric('Wickets (filtered)', int(total_wickets)) col4.metric('Unique players', int(unique_players))

st.markdown('---')

Matches per Season

matches_per_season = matches[matches['season'].isin(selected_seasons)].groupby('season').size().reset_index(name='matches') fig_mps = px.bar(matches_per_season, x='season', y='matches', title='Matches per Season (selected)') st.plotly_chart(fig_mps, use_container_width=True)

Runs per Over (aggregated)

runs_per_over = f_deliveries.groupby('over')['total_runs'].sum().reset_index() fig_over = px.line(runs_per_over, x='over', y='total_runs', markers=True, title='Runs by Over (filtered)') st.plotly_chart(fig_over, use_container_width=True)

Top batsmen and bowlers

st.header('Top Performers') with st.expander('Top batsmen (by runs)'): batsman_runs = f_deliveries.groupby('batsman')['batsman_runs'].sum().reset_index().sort_values('batsman_runs', ascending=False).head(15) st.table(batsman_runs.rename(columns={'batsman':'Player','batsman_runs':'Runs'}).reset_index(drop=True))

with st.expander('Top bowlers (by wickets)'): # dismissals: count non-null dismissal_kind except 'run out' if you prefer wickets = f_deliveries[f_deliveries['dismissal_kind'].notna()] wickets = wickets[~wickets['dismissal_kind'].isin(['run out','retired hurt'])] bowler_wickets = wickets.groupby('bowler').size().reset_index(name='Wickets').sort_values('Wickets', ascending=False).head(15) st.table(bowler_wickets.rename(columns={'bowler':'Player'}).reset_index(drop=True))

st.markdown('---')

Team wins

st.header('Team Wins') team_wins = f_matches.groupby('winner').size().reset_index(name='wins').sort_values('wins', ascending=False) fig_wins = px.bar(team_wins, x='winner', y='wins', title='Wins by Team (filtered)') st.plotly_chart(fig_wins, use_container_width=True)

Venue analysis

st.header('Venue & Scoring') venue_runs = f_deliveries.groupby('venue')['total_runs'].sum().reset_index().sort_values('total_runs', ascending=False).head(20) fig_venue = px.bar(venue_runs, x='venue', y='total_runs', title='Top venues by aggregate runs') st.plotly_chart(fig_venue, use_container_width=True)

Head-to-head

st.header('Head-to-head') if selected_team == 'All': st.info('Select a team from the sidebar to see head-to-head summaries.') else: opponents = [t for t in teams if t != selected_team] opp = st.selectbox('Opponent', ['All'] + opponents) if opp == 'All': hh = f_matches.copy() else: hh = f_matches[((f_matches['team1']==selected_team)&(f_matches['team2']==opp))|((f_matches['team2']==selected_team)&(f_matches['team1']==opp))] hh_summary = hh.groupby('winner').size().reset_index(name='wins').sort_values('wins', ascending=False) st.table(hh_summary)

st.markdown('---')

Time series: runs per season

st.header('Season-wise runs') runs_season = deliveries[deliveries['match_id'].isin(matches[matches['season'].isin(selected_seasons)]['id'])].groupby(matches.set_index('id').loc[lambda df: df['season'].isin(selected_seasons)]['season'].values).sum(numeric_only=True)

simpler approach:

runs_season = pd.merge(deliveries, matches[['id','season']], left_on='match_id', right_on='id') runs_season = runs_season[runs_season['season'].isin(selected_seasons)].groupby('season')['total_runs'].sum().reset_index() fig_rs = px.line(runs_season, x='season', y='total_runs', markers=True, title='Total Runs by Season') st.plotly_chart(fig_rs, use_container_width=True)

st.markdown('---')

Download cleaned sample

st.header('Download sample data') if st.button('Download filtered deliveries (CSV)'): st.download_button('Click to download', data=f_deliveries.to_csv(index=False), file_name='filtered_deliveries.csv', mime='text/csv')

st.caption('Dashboard built with Streamlit • Data source: Kaggle IPL datasets (matches.csv, deliveries.csv)')

End of file
