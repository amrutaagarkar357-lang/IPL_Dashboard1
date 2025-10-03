"""
IPL Dashboard — Streamlit web UI with a safe CLI/HTML fallback

This file was created to be runnable in two modes:

1) Streamlit mode (preferred) — if `streamlit` is installed, the app will run as an interactive
   Streamlit web app with file upload or GitHub-raw URL inputs.

2) CLI / Offline HTML mode (fallback) — if `streamlit` is NOT installed (common in restricted
   sandboxes), the script will run in a command-line mode that:
     - Loads the CSVs from local paths or HTTP raw URLs
     - Performs the same preprocessing and aggregations as the Streamlit version
     - Produces an `index.html` report with interactive Plotly charts (if Plotly is available),
       or otherwise writes aggregated CSVs to disk.

Why this change? In some environments `import streamlit as st` raises:
    ModuleNotFoundError: No module named 'streamlit'

Since you can't install packages from inside a restricted sandbox, this script
handles that gracefully and still produces useful output.

How to use
----------
- To run as Streamlit app (if Streamlit is available):
    streamlit run ipl_streamlit_dashboard.py

- To run in CLI/offline mode (works without Streamlit):
    python ipl_streamlit_dashboard.py --matches PATH_OR_URL --deliveries PATH_OR_URL --outdir report

- To run built-in tests:
    python ipl_streamlit_dashboard.py --test

Notes
-----
- This script requires Python 3.8+ and pandas. Plotly is optional but recommended for
  interactive HTML output. If Plotly is not present, aggregated CSVs will be written.
- The script is defensive about missing or variant column names (e.g., `id` vs `match_id`).

"""

import os
import sys
import argparse
import textwrap
from typing import Tuple, Dict

# Try to import streamlit — if unavailable, we'll work in CLI mode
try:
    import streamlit as st  # type: ignore
    STREAMLIT_AVAILABLE = True
except Exception:
    st = None
    STREAMLIT_AVAILABLE = False

# Core data libraries
try:
    import pandas as pd
    import numpy as np
except Exception as e:
    print("ERROR: This script requires pandas and numpy. Please install them (pip install pandas numpy)")
    raise

# Optional plotting library (used for both Streamlit & HTML fallback)
try:
    import plotly.express as px
    import plotly.io as pio
    PLOTLY_AVAILABLE = True
except Exception:
    PLOTLY_AVAILABLE = False


# -------------------
# Utility functions
# -------------------

def normalize_match_id_column(matches: pd.DataFrame, deliveries: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Unify the join key between matches and deliveries to 'match_id'."""
    matches = matches.copy()
    deliveries = deliveries.copy()

    # matches: rename 'id' -> 'match_id' if needed
    if 'match_id' not in matches.columns and 'id' in matches.columns:
        matches = matches.rename(columns={'id': 'match_id'})

    # deliveries: rename 'id' -> 'match_id' if needed
    if 'match_id' not in deliveries.columns and 'id' in deliveries.columns:
        deliveries = deliveries.rename(columns={'id': 'match_id'})

    # If matches has 'match_id' but deliveries has 'id', rename deliveries
    if 'match_id' in matches.columns and 'match_id' not in deliveries.columns and 'id' in deliveries.columns:
        deliveries = deliveries.rename(columns={'id': 'match_id'})

    return matches, deliveries


def preprocess_deliveries(deliveries: pd.DataFrame) -> pd.DataFrame:
    """Compute useful derived columns on deliveries (total_runs, legal_delivery, is_wicket).

    This function does not modify the original DataFrame (returns a copy).
    """
    d = deliveries.copy()

    # Ensure numeric fields exist and fill missing with 0
    if 'batsman_runs' in d.columns:
        d['batsman_runs'] = pd.to_numeric(d['batsman_runs'], errors='coerce').fillna(0).astype(int)
    if 'extra_runs' in d.columns:
        d['extra_runs'] = pd.to_numeric(d['extra_runs'], errors='coerce').fillna(0).astype(int)

    # total_runs: prefer the explicit column if present, otherwise compute batsman_runs + extra_runs
    if 'total_runs' not in d.columns:
        if 'batsman_runs' in d.columns:
            d['total_runs'] = d.get('batsman_runs', 0) + d.get('extra_runs', 0)
        else:
            # fallback to 0 if no finer-grained columns exist
            d['total_runs'] = 0

    d['wide_runs'] = d.get('wide_runs', 0).fillna(0).astype(int)
    d['noball_runs'] = d.get('noball_runs', 0).fillna(0).astype(int)

    # legal delivery excludes wides and no-balls
    d['legal_delivery'] = ((d['wide_runs'] == 0) & (d['noball_runs'] == 0)).astype(int)

    # is_wicket: presence of player_dismissed
    if 'player_dismissed' in d.columns:
        d['is_wicket'] = d['player_dismissed'].notna().astype(int)
    else:
        d['is_wicket'] = 0

    return d


def merge_matches_deliveries(matches: pd.DataFrame, deliveries: pd.DataFrame) -> pd.DataFrame:
    """Merge deliveries with selected match-level columns (season, venue, winner, team1, team2).

    If match_id is missing we return deliveries copy (some visuals will be limited).
    """
    if 'match_id' in deliveries.columns and 'match_id' in matches.columns:
        cols = [c for c in ['match_id', 'season', 'winner', 'venue', 'team1', 'team2'] if c in matches.columns]
        merged = deliveries.merge(matches[cols], how='left', on='match_id')
        return merged
    else:
        return deliveries.copy()


def compute_figs_and_tables(merged: pd.DataFrame, matches: pd.DataFrame, selected_team: str = 'All Teams', selected_season: str = 'All Seasons') -> Tuple[Dict[str, object], Dict[str, pd.DataFrame]]:
    """Compute Plotly figures and key aggregated DataFrames.

    Returns:
        figs: dict[str, plotly figure] — may be empty if Plotly isn't available
        tables: dict[str, pd.DataFrame]
    """
    figs = {}
    tables = {}

    # Basic KPIs
    total_matches = matches['match_id'].nunique() if 'match_id' in matches.columns else matches.shape[0]
    total_runs = int(merged['total_runs'].sum()) if 'total_runs' in merged.columns else 0
    total_wickets = int(merged['is_wicket'].sum()) if 'is_wicket' in merged.columns else 0

    tables['kpis'] = pd.DataFrame({
        'metric': ['total_matches', 'total_runs', 'total_wickets'],
        'value': [total_matches, total_runs, total_wickets]
    })

    # Top batsmen
    if 'batsman' in merged.columns:
        batsman_group = merged.groupby('batsman').agg(
            runs=('batsman_runs', 'sum') if 'batsman_runs' in merged.columns else ('total_runs', 'sum'),
            balls=('legal_delivery', 'sum')
        ).reset_index()
        batsman_group['strike_rate'] = batsman_group.apply(lambda r: (r['runs'] / r['balls'] * 100) if r['balls'] > 0 else 0, axis=1)
        top_bats = batsman_group.sort_values('runs', ascending=False).head(15)
        tables['top_batsmen'] = top_bats

        if PLOTLY_AVAILABLE:
            figs['top_bats_runs'] = px.bar(top_bats, x='batsman', y='runs', title='Top Batsmen by Runs', text='runs')
            figs['top_bats_strike'] = px.scatter(top_bats, x='batsman', y='strike_rate', size='runs', title='Strike Rate (size=runs)')

    # Top bowlers
    if 'bowler' in merged.columns:
        bowl_group = merged.groupby('bowler').agg(
            runs_conceded=('total_runs', 'sum'),
            legal_balls=('legal_delivery', 'sum'),
            wickets=('is_wicket', 'sum')
        ).reset_index()
        bowl_group['overs'] = bowl_group['legal_balls'] / 6
        bowl_group['economy'] = bowl_group.apply(lambda r: (r['runs_conceded'] / r['overs']) if r['overs'] > 0 else np.nan, axis=1)
        top_bowl = bowl_group.sort_values('wickets', ascending=False).head(15)
        tables['top_bowlers'] = top_bowl

        if PLOTLY_AVAILABLE:
            figs['top_bowl_wkts'] = px.bar(top_bowl, x='bowler', y='wickets', title='Top Bowlers by Wickets', text='wickets')
            figs['bowl_economy'] = px.scatter(top_bowl.sort_values('economy'), x='bowler', y='economy', size='wickets', title='Economy (size=wickets)')

    # Team winning trends
    if 'winner' in matches.columns and 'season' in matches.columns:
        matches_filtered = matches.copy()
        if selected_season != 'All Seasons':
            matches_filtered = matches_filtered[matches_filtered['season'].astype(str) == str(selected_season)]

        if selected_team == 'All Teams':
            wins_by_season = matches_filtered.groupby('season')['winner'].value_counts().unstack(fill_value=0)
            tables['wins_by_season'] = wins_by_season
        else:
            team_wins = matches_filtered[matches_filtered['winner'] == selected_team].groupby('season')['match_id'].count().reset_index()
            team_wins.columns = ['season', 'wins']
            tables['team_wins'] = team_wins
            if PLOTLY_AVAILABLE:
                figs['team_wins'] = px.line(team_wins, x='season', y='wins', markers=True, title=f'Wins per season — {selected_team}')

    # Stadium trends
    if 'venue' in matches.columns:
        if selected_team == 'All Teams':
            top_venues = matches['venue'].value_counts().head(10).reset_index()
            top_venues.columns = ['venue', 'count']
            tables['top_venues'] = top_venues
            if PLOTLY_AVAILABLE:
                figs['top_venues'] = px.bar(top_venues, x='venue', y='count', text='count', title='Top Venues by Matches Hosted')
        else:
            team_wins_matches = matches[matches['winner'] == selected_team]
            if selected_season != 'All Seasons':
                team_wins_matches = team_wins_matches[team_wins_matches['season'].astype(str) == str(selected_season)]
            venue_counts = team_wins_matches['venue'].value_counts().head(10).reset_index()
            venue_counts.columns = ['venue', 'wins']
            tables['team_venue_wins'] = venue_counts
            if not venue_counts.empty and PLOTLY_AVAILABLE:
                figs['team_venue_wins'] = px.bar(venue_counts, x='venue', y='wins', text='wins', title=f'Top venues where {selected_team} won')

    # Head-to-head (simple matrix)
    if set(['team1', 'team2', 'winner']).issubset(matches.columns):
        pairs = matches.dropna(subset=['winner', 'team1', 'team2']).copy()
        win_counts = pairs.groupby(['winner', 'team2']).size().unstack(fill_value=0)
        tables['head_to_head'] = win_counts

    return figs, tables


# -------------------
# Output helpers
# -------------------

def write_html_report(figs: Dict[str, object], tables: Dict[str, pd.DataFrame], outdir: str) -> str:
    """Write a single HTML report combining Plotly figures and simple table dumps.

    Returns path to the written index.html.
    """
    os.makedirs(outdir, exist_ok=True)
    html_parts = ["<html><head><meta charset='utf-8'><title>IPL Report</title></head><body>"]

    # KPIs
    if 'kpis' in tables:
        html_parts.append('<h1>Key Metrics</h1>')
        html_parts.append(tables['kpis'].to_html(index=False))

    for key, fig in figs.items():
        html_parts.append(f"<h2>{key.replace('_', ' ').title()}</h2>")
        # Use plotly to produce figure HTML
        try:
            div = pio.to_html(fig, full_html=False, include_plotlyjs='cdn')
            html_parts.append(div)
        except Exception:
            html_parts.append("<p>[Could not render figure]</p>")

    # Tables
    html_parts.append('<h1>Aggregated tables</h1>')
    for name, df in tables.items():
        html_parts.append(f"<h2>{name.replace('_', ' ').title()}</h2>")
        html_parts.append(df.to_html())

    html_parts.append("</body></html>")
    index_path = os.path.join(outdir, 'index.html')
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(html_parts))

    # Also write CSVs for main tables for convenience
    for name, df in tables.items():
        try:
            df.to_csv(os.path.join(outdir, f"{name}.csv"))
        except Exception:
            pass

    return index_path


# -------------------
# Streamlit app runner
# -------------------

def run_streamlit_app():
    """Run the interactive Streamlit app. This function only runs when Streamlit is available."""
    st.set_page_config(page_title='IPL Dashboard — Step by Step', layout='wide')
    st.title('🏏 IPL Analytics Dashboard — Streamlit mode')
    st.markdown('Upload `matches.csv` and `deliveries.csv` or paste raw GitHub URLs.')

    data_source = st.sidebar.radio('Data source', ['Upload CSV files', 'GitHub raw URLs'])

    matches = None
    deliveries = None

    if data_source == 'Upload CSV files':
        m_file = st.sidebar.file_uploader('Upload matches.csv', type=['csv'], key='mfile')
        d_file = st.sidebar.file_uploader('Upload deliveries.csv', type=['csv'], key='dfile')
        if m_file is not None and d_file is not None:
            matches = pd.read_csv(m_file)
            deliveries = pd.read_csv(d_file)
        else:
            st.info('Please upload both CSV files or switch to GitHub raw URLs.')
            st.stop()
    else:
        st.sidebar.write('Paste raw GitHub URLs (click "Raw" on GitHub and copy the URL).')
        m_url = st.sidebar.text_input('Matches raw URL')
        d_url = st.sidebar.text_input('Deliveries raw URL')
        if not m_url or not d_url:
            st.info('Please provide both URLs or upload files.')
            st.stop()
        try:
            matches = pd.read_csv(m_url)
            deliveries = pd.read_csv(d_url)
        except Exception as e:
            st.sidebar.error(f'Unable to load CSVs from the provided URLs: {e}')
            st.stop()

    # Normalization & preprocessing
    matches, deliveries = normalize_match_id_column(matches, deliveries)
    deliveries = preprocess_deliveries(deliveries)
    merged = merge_matches_deliveries(matches, deliveries)

    # Filters
    seasons = sorted(matches['season'].dropna().unique().tolist()) if 'season' in matches.columns else []
    selected_season = st.sidebar.selectbox('Season', ['All Seasons'] + [str(s) for s in seasons])

    if set(['team1', 'team2']).issubset(matches.columns):
        teams = sorted(pd.unique(matches[['team1', 'team2']].values.ravel('K')).tolist())
    else:
        teams = sorted(matches['team1'].dropna().unique().tolist()) if 'team1' in matches.columns else []

    selected_team = st.sidebar.selectbox('Team', ['All Teams'] + teams)

    # Apply team/season filters to merged as in the original app
    df_merged = merged.copy()
    if selected_season != 'All Seasons' and 'season' in df_merged.columns:
        df_merged = df_merged[df_merged['season'].astype(str) == str(selected_season)]
    if selected_team != 'All Teams' and 'match_id' in matches.columns:
        match_ids_team = matches[(matches['team1'] == selected_team) | (matches['team2'] == selected_team)]['match_id'].unique()
        df_merged = df_merged[df_merged['match_id'].isin(match_ids_team)]

    # Compute figures & tables
    figs, tables = compute_figs_and_tables(df_merged, matches, selected_team=selected_team, selected_season=selected_season)

    # Show KPIs
    st.header('Key Metrics')
    kpis = tables.get('kpis')
    if kpis is not None:
        cols = st.columns(len(kpis))
        for c, (_, row) in zip(cols, kpis.iterrows()):
            c.metric(row['metric'], row['value'])

    # Render figures (if any)
    for name, fig in figs.items():
        st.subheader(name.replace('_', ' ').title())
        st.plotly_chart(fig, use_container_width=True)

    # Show data tables
    st.subheader('Aggregated tables')
    for name, df in tables.items():
        st.markdown(f'**{name.replace("_", " ").title()}**')
        st.dataframe(df)

    st.success('Streamlit dashboard loaded — interact with the sidebar to explore the data!')


# -------------------
# CLI / offline runner
# -------------------

def run_cli(matches_path: str, deliveries_path: str, outdir: str = 'ipl_report') -> None:
    """Run a headless mode that generates an HTML report (or CSVs) at `outdir`.

    `matches_path` and `deliveries_path` are either local file paths or HTTP(S) URLs.
    """
    print('\nRunning in CLI / offline mode')
    print(f'Loading matches from: {matches_path}')
    print(f'Loading deliveries from: {deliveries_path}')

    try:
        matches = pd.read_csv(matches_path)
    except Exception as e:
        print(f'Failed to load matches CSV: {e}')
        return

    try:
        deliveries = pd.read_csv(deliveries_path)
    except Exception as e:
        print(f'Failed to load deliveries CSV: {e}')
        return

    matches, deliveries = normalize_match_id_column(matches, deliveries)
    deliveries = preprocess_deliveries(deliveries)
    merged = merge_matches_deliveries(matches, deliveries)

    # Default filters: All Teams / All Seasons
    figs, tables = compute_figs_and_tables(merged, matches, selected_team='All Teams', selected_season='All Seasons')

    # Write output
    os.makedirs(outdir, exist_ok=True)

    if PLOTLY_AVAILABLE and figs:
        index_path = write_html_report(figs, tables, outdir=outdir)
        print(f'HTML report written to: {index_path}')
    else:
        # Still write tables to CSV
        for name, df in tables.items():
            csv_path = os.path.join(outdir, f"{name}.csv")
            try:
                df.to_csv(csv_path)
                print(f'Wrote {csv_path}')
            except Exception as e:
                print(f'Failed to write {name} to CSV: {e}')
        print('\nPlotly not available or no figures generated; CSV exports written instead.')

    print('\nDone.')


# -------------------
# Tests: small synthetic dataset to validate the pipeline
# -------------------

def run_tests(outdir: str = 'test_report') -> None:
    """Create small synthetic datasets to test preprocessing and report generation."""
    print('\nRunning built-in tests (synthetic sample data)')

    matches = pd.DataFrame({
        'match_id': [1, 2],
        'season': [2020, 2020],
        'team1': ['Mumbai Indians', 'Chennai Super Kings'],
        'team2': ['Royal Challengers Bangalore', 'Kolkata Knight Riders'],
        'winner': ['Mumbai Indians', 'Kolkata Knight Riders'],
        'venue': ['Wankhede', 'Eden Gardens']
    })

    deliveries = pd.DataFrame({
        'match_id': [1, 1, 1, 2, 2, 2],
        'inning': [1, 1, 2, 1, 1, 2],
        'batting_team': ['Mumbai Indians', 'Mumbai Indians', 'Royal Challengers Bangalore', 'Chennai Super Kings', 'Chennai Super Kings', 'Kolkata Knight Riders'],
        'bowling_team': ['Royal Challengers Bangalore', 'Royal Challengers Bangalore', 'Mumbai Indians', 'Kolkata Knight Riders', 'Kolkata Knight Riders', 'Chennai Super Kings'],
        'batsman': ['A', 'B', 'C', 'D', 'E', 'F'],
        'bowler': ['x', 'y', 'x', 'z', 'z', 'w'],
        'batsman_runs': [4, 6, 2, 3, 4, 1],
        'extra_runs': [0, 0, 0, 0, 1, 0],
        'wide_runs': [0, 0, 0, 0, 0, 0],
        'noball_runs': [0, 0, 0, 0, 0, 0],
        'player_dismissed': [None, 'B', None, None, None, 'F']
    })

    matches, deliveries = normalize_match_id_column(matches, deliveries)
    deliveries = preprocess_deliveries(deliveries)
    merged = merge_matches_deliveries(matches, deliveries)

    figs, tables = compute_figs_and_tables(merged, matches)

    if PLOTLY_AVAILABLE and figs:
        index_path = write_html_report(figs, tables, outdir=outdir)
        print(f'Test HTML report written to: {index_path}')
    else:
        os.makedirs(outdir, exist_ok=True)
        for name, df in tables.items():
            csv_path = os.path.join(outdir, f"{name}.csv")
            df.to_csv(csv_path)
            print(f'Wrote test CSV: {csv_path}')

    print('Tests finished.')


# -------------------
# Main entrypoint
# -------------------

def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]

    parser = argparse.ArgumentParser(description='IPL dashboard (Streamlit or CLI/HTML fallback)')
    parser.add_argument('--matches', help='Path or URL to matches.csv')
    parser.add_argument('--deliveries', help='Path or URL to deliveries.csv')
    parser.add_argument('--outdir', default='ipl_report', help='Output directory for HTML/CSV report')
    parser.add_argument('--test', action='store_true', help='Run built-in tests with a small synthetic dataset')

    args = parser.parse_args(argv)

    if args.test:
        run_tests(outdir=args.outdir)
        return

    if STREAMLIT_AVAILABLE:
        # If Streamlit is available, prefer running the Streamlit UI. The user can still run CLI with --matches + --deliveries.
        if args.matches and args.deliveries:
            # CLI invocation with Streamlit installed — user explicitly provided paths: run offline generator
            run_cli(args.matches, args.deliveries, outdir=args.outdir)
        else:
            # Launch Streamlit UI
            run_streamlit_app()
    else:
        # Streamlit not available -> require matches & deliveries for CLI mode
        if not args.matches or not args.deliveries:
            print(textwrap.dedent("""
                Streamlit is not available in this environment (ModuleNotFoundError: streamlit).
                Falling back to CLI/offline mode. Please provide --matches and --deliveries paths or URLs.

                Example:
                  python ipl_streamlit_dashboard.py --matches data/matches.csv --deliveries data/deliveries.csv --outdir report

                Or run the built-in tests:
                  python ipl_streamlit_dashboard.py --test
                """))
            return
        run_cli(args.matches, args.deliveries, outdir=args.outdir)


if __name__ == '__main__':
    main()
