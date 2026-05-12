# app.py
#
# PURPOSE: Streamlit UI for the Football Analytics App.
# Run with: streamlit run src/app.py (from the project root with venv active)
#
# HOW STREAMLIT WORKS:
# Streamlit re-runs the entire script from top to bottom every time the user
# interacts with any widget (dropdown, button, etc.). State is managed through
# st.session_state. @st.cache_data prevents re-fetching data on every re-run.

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import streamlit as st
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io
import warnings
warnings.filterwarnings('ignore')

import data_loader
from passing_network import draw_passing_network
from heat_map import draw_heat_map
from shot_map import draw_shot_map
from press_map import draw_press_map

# ── PAGE CONFIG ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title='Football Analytics',
    page_icon='⚽',
    layout='wide'
)

st.title('⚽ Football Analytics')

# ── SIDEBAR — MATCH SELECTION ──────────────────────────────────────────────────
with st.sidebar:
    st.header('Match Selection')

    # Step 1: Load all available competitions
    competitions = data_loader.get_competitions()

    # Build a human-readable label for each competition+season row
    # e.g. "Premier League 2003/04 (England)"
    competitions['label'] = (
        competitions['competition_name'] + ' ' +
        competitions['season_name'] + ' (' +
        competitions['country_name'] + ')'
    )
    competitions = competitions.sort_values('label')

    selected_label = st.selectbox('Competition & Season', competitions['label'].tolist())
    selected_row   = competitions[competitions['label'] == selected_label].iloc[0]

    competition_id = int(selected_row['competition_id'])
    season_id      = int(selected_row['season_id'])

    # Step 2: Load matches for the selected competition+season
    matches = data_loader.get_matches(competition_id, season_id)

    # Build a human-readable label: "Arsenal 4-2 Liverpool (2003-11-15)"
    matches['label'] = (
        matches['home_team'] + ' ' +
        matches['home_score'].astype(str) + '–' +
        matches['away_score'].astype(str) + ' ' +
        matches['away_team'] + ' (' +
        matches['match_date'].astype(str) + ')'
    )
    matches = matches.sort_values('match_date', ascending=False)

    selected_match_label = st.selectbox('Match', matches['label'].tolist())
    selected_match = matches[matches['label'] == selected_match_label].iloc[0]
    match_id = int(selected_match['match_id'])

    # Step 3: Team selection (home or away)
    home_team = selected_match['home_team']
    away_team = selected_match['away_team']
    selected_team = st.radio('Team to analyse', [home_team, away_team])

    # Step 4: Analysis type
    st.divider()
    st.header('Analysis')
    analysis_options = ['Passing Network', 'Heat Map', 'Shot Map', 'Press Map']
    selected_analysis = st.selectbox('Analysis Type', analysis_options)

    # Step 5: Player selector — only shown for Heat Map
    selected_player = None
    if selected_analysis == 'Heat Map':
        events_preview = data_loader.get_events(match_id)
        team_players = sorted(
            events_preview[
                (events_preview['team'] == selected_team) &
                (events_preview['player'].notna())
            ]['player'].unique().tolist()
        )
        selected_player = st.selectbox('Player', team_players)

    # Step 6: Run button
    st.divider()
    run = st.button('Generate Visualization', type='primary', use_container_width=True)

# ── MAIN AREA — VISUALIZATION ──────────────────────────────────────────────────
# Build a match label for chart titles
score_label = (
    f"{selected_match['home_team']} "
    f"{selected_match['home_score']}–{selected_match['away_score']} "
    f"{selected_match['away_team']}"
)
match_label = f"{score_label} | {selected_row['competition_name']} {selected_row['season_name']}"

if run:
    with st.spinner('Loading match data...'):
        events = data_loader.get_events(match_id)

    with st.spinner(f'Drawing {selected_analysis}...'):
        try:
            if selected_analysis == 'Passing Network':
                fig = draw_passing_network(events, selected_team, match_label)
            elif selected_analysis == 'Heat Map':
                fig = draw_heat_map(events, selected_player, selected_team, match_label)
            elif selected_analysis == 'Shot Map':
                fig = draw_shot_map(events, selected_team, match_label)
            elif selected_analysis == 'Press Map':
                fig = draw_press_map(events, selected_team, match_label)

            st.pyplot(fig)

            # Save the figure to a bytes buffer for the download button
            buf = io.BytesIO()
            fig.savefig(buf, format='png', dpi=150, bbox_inches='tight')
            buf.seek(0)

            filename = (
                f"{selected_team.replace(' ', '_').lower()}_"
                f"{selected_analysis.replace(' ', '_').lower()}.png"
            )
            st.download_button(
                label='Download Image',
                data=buf,
                file_name=filename,
                mime='image/png'
            )

            plt.close(fig)

        except ValueError as e:
            st.error(str(e))
        except Exception as e:
            st.error(f'Something went wrong: {e}')

else:
    st.info('Configure your selection in the sidebar and click **Generate Visualization**.')
