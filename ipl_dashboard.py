"""
Easy IPL Dashboard (streamlit-safe)

This script was rewritten to avoid failing when `streamlit` is not installed.
Behavior:
 - If `streamlit` is available: runs as an interactive Streamlit app (recommended).
 - If `streamlit` is NOT available: falls back to a non-interactive mode that
   creates three PNG charts in the current directory and prints instructions.

Usage:
 - Place `matches.csv` (Kaggle IPL dataset) in the same folder as this script.
 - Preferred (interactive): `pip install streamlit pandas matplotlib seaborn` then
   `streamlit run this_script.py`.
 - Fallback (no streamlit): `python this_script.py` — it will save PNGs.

"""

import sys
import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from textwrap import dedent

# Try to import streamlit; decide mode based on availability
try:
    import streamlit as st
    STREAMLIT_AVAILABLE = True
except Exception:
    STREAMLIT_AVAILABLE = False

# Common plotting function
def plot_top_winning_teams(matches, save_path=None, use_streamlit=False):
    df = matches.copy()
    wins = df['winner'].dropna().value_counts().reset_index()
    wins.columns = ['Team', 'Wins']
    wins = wins.head(10)

    fig, ax = plt.subplots(figsize=(8, 5))
    sns.barplot(x='Wins', y='Team', data=wins, ax=ax)
    ax.set_title('Top 10 Teams by Wins')
    ax.set_xlabel('Wins')
    ax.set_ylabel('Team')
    plt.tight_layout()

    if use_streamlit:
        st.pyplot(fig)
    else:
        path = save_path or 'top_winning_teams.png'
        fig.savefig(path)
        plt.close(fig)
        print(f"Saved: {path}")


def plot_matches_per_season(matches, save_path=None, use_streamlit=False):
    df = matches.copy()
    # Ensure season is numeric for correct sorting
    if df['season'].dtype == object:
        try:
            df['season'] = pd.to_numeric(df['season'], errors='coerce')
        except Exception:
            pass
    season_counts = df.groupby('season')['id'].nunique().reset_index()
    season_counts = season_counts.sort_values('season')
    season_counts.columns = ['Season', 'Matches']

    fig, ax = plt.subplots(figsize=(8, 4))
    sns.lineplot(x='Season', y='Matches', data=season_counts, marker='o', ax=ax)
    ax.set_title('Matches per Season')
    ax.set_xlabel('Season')
    ax.set_ylabel('Number of Matches')
    plt.tight_layout()

    if use_streamlit:
        st.pyplot(fig)
    else:
        path = save_path or 'matches_per_season.png'
        fig.savefig(path)
        plt.close(fig)
        print(f"Saved: {path}")


def plot_top_venues(matches, save_path=None, use_streamlit=False):
    df = matches.copy()
    venues = df['venue'].fillna('Unknown').value_counts().head(10).reset_index()
    venues.columns = ['Venue', 'Matches']

    fig, ax = plt.subplots(figsize=(8, 5))
    sns.barplot(x='Matches', y='Venue', data=venues, ax=ax)
    ax.set_title('Top 10 Venues by Matches Hosted')
    ax.set_xlabel('Matches')
    ax.set_ylabel('Venue')
    plt.tight_layout()

    if use_streamlit:
        st.pyplot(fig)
    else:
        path = save_path or 'top_venues.png'
        fig.savefig(path)
        plt.close(fig)
        print(f"Saved: {path}")


def load_matches(path='matches.csv'):
    if not os.path.exists(path):
        raise FileNotFoundError(f"Could not find '{path}'. Please download 'matches.csv' from the Kaggle IPL dataset and place it in this folder.")
    df = pd.read_csv(path)
    # Basic sanity checks
    if 'id' not in df.columns:
        # some versions use different column names - attempt to infer
        if 'match_id' in df.columns:
            df = df.rename(columns={'match_id': 'id'})
        else:
            # create a synthetic id
            df = df.reset_index().rename(columns={'index': 'id'})
    return df


def run_streamlit_app(matches):
    st.set_page_config(page_title='Easy IPL Dashboard', layout='wide')
    st.title('🏏 Easy IPL Dashboard')
    st.markdown('A minimal IPL dashboard — if Streamlit is not installed the script saves PNGs instead.')

    st.subheader('Top Winning Teams')
    plot_top_winning_teams(matches, use_streamlit=True)

    st.subheader('Matches per Season')
    plot_matches_per_season(matches, use_streamlit=True)

    st.subheader('Top Venues by Matches Hosted')
    plot_top_venues(matches, use_streamlit=True)

    st.markdown('---')
    st.info(dedent("""
    💡 Steps to run:
    1. Download 'matches.csv' from Kaggle IPL dataset and place it in the same folder as this script.
    2. Install dependencies: `pip install streamlit pandas matplotlib seaborn`.
    3. Run: `streamlit run this_script.py` (replace with actual filename).
    """))


def run_fallback_mode(matches):
    print('\nStreamlit is NOT available in this environment — running fallback mode.\n')
    print('Charts will be saved as PNG files in the current directory.')
    plot_top_winning_teams(matches, save_path='top_winning_teams.png', use_streamlit=False)
    plot_matches_per_season(matches, save_path='matches_per_season.png', use_streamlit=False)
    plot_top_venues(matches, save_path='top_venues.png', use_streamlit=False)

    print('\nTo get an interactive experience, install Streamlit and run:')
    print('  pip install streamlit pandas matplotlib seaborn')
    print('  streamlit run this_script.py')


def main():
    try:
        matches = load_matches('matches.csv')
    except FileNotFoundError as e:
        msg = dedent(f"""
        ERROR: {e}

        Solution:
        1. Go to the Kaggle IPL dataset (https://www.kaggle.com/competitions/ipl or search "IPL matches.csv Kaggle").
        2. Download 'matches.csv' and put it in the same folder as this script.
        3. Re-run (either `streamlit run this_script.py` or `python this_script.py`).
        """)
        print(msg)
        sys.exit(1)

    if STREAMLIT_AVAILABLE:
        try:
            run_streamlit_app(matches)
        except Exception as e:
            # If something unexpected fails in Streamlit, fall back to PNG generation
            print('Streamlit mode failed with error:', e)
            print('Falling back to PNG generation...')
            run_fallback_mode(matches)
    else:
        run_fallback_mode(matches)


if __name__ == '__main__':
    main()
