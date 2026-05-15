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
from image_utils import stitch_figures
from passing_network import draw_passing_network
from heat_map import draw_heat_map
from shot_map import draw_shot_map
from press_map import draw_press_map
from content_generator import generate_content

# ── PAGE CONFIG ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title='Football Analytics',
    page_icon='⚽',
    layout='wide'
)

st.title('⚽ Football Analytics')

# ── SIDEBAR ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header('Match Selection')

    competitions = data_loader.get_competitions()

    countries = sorted(competitions['country_name'].unique().tolist())
    selected_country = st.selectbox('Country', countries)

    # Reset League and Season when Country changes
    if st.session_state.get('_prev_country') != selected_country:
        st.session_state.pop('League', None)
        st.session_state.pop('Season', None)
        st.session_state['_prev_country'] = selected_country

    country_comps = competitions[competitions['country_name'] == selected_country]
    leagues = sorted(country_comps['competition_name'].unique().tolist())
    selected_league = st.selectbox('League', leagues, key='League')

    # Reset Season when League changes
    if st.session_state.get('_prev_league') != selected_league:
        st.session_state.pop('Season', None)
        st.session_state['_prev_league'] = selected_league

    league_comps = (
        country_comps[country_comps['competition_name'] == selected_league]
        .sort_values('season_name', ascending=False)
    )
    seasons = league_comps['season_name'].tolist()
    selected_season = st.selectbox('Season', seasons, key='Season')

    selected_row = league_comps[league_comps['season_name'] == selected_season].iloc[0]
    competition_id = int(selected_row['competition_id'])
    season_id      = int(selected_row['season_id'])

    matches = data_loader.get_matches(competition_id, season_id)

    matches['label'] = (
        matches['match_date'].astype(str).str[:7] + ' — ' +
        matches['home_team'] + ' ' +
        matches['home_score'].astype(str) + '–' +
        matches['away_score'].astype(str) + ' ' +
        matches['away_team']
    )
    matches = matches.sort_values('match_date', ascending=False)

    selected_match_label = st.selectbox('Match', matches['label'].tolist())
    selected_match = matches[matches['label'] == selected_match_label].iloc[0]
    match_id = int(selected_match['match_id'])

    home_team = selected_match['home_team']
    away_team = selected_match['away_team']
    selected_team = st.radio('Team to analyse', [home_team, away_team])

    st.divider()
    st.header('Analysis')

    ANALYSIS_LABELS = {
        '🕸️ Passing Network': 'Passing Network',
        '🌡️ Heat Map':        'Heat Map',
        '🎯 Shot Map':        'Shot Map',
        '⚡ Press Map':       'Press Map',
    }

    selected_labels = st.pills(
        label='Analysis',
        options=list(ANALYSIS_LABELS.keys()),
        selection_mode='multi',
        default=['🕸️ Passing Network'],
        label_visibility='collapsed',
    )
    selected_analyses: list[str] = [ANALYSIS_LABELS[label] for label in (selected_labels or [])]

    selected_player: str | None = None
    if 'Heat Map' in selected_analyses:
        events_preview = data_loader.get_events(match_id)
        team_players = sorted(
            events_preview[
                (events_preview['team'] == selected_team) &
                (events_preview['player'].notna())
            ]['player'].unique().tolist()
        )
        selected_player = st.selectbox('Player (Heat Map)', team_players)

    st.divider()
    n = len(selected_analyses)
    btn_label = f'Generate {n} Visualizations' if n > 1 else 'Generate Visualization'
    run = st.button(
        btn_label,
        type='primary',
        use_container_width=True,
        disabled=(n == 0),
    )

# ── MAIN AREA ─────────────────────────────────────────────────────────────────
score_label = (
    f"{selected_match['home_team']} "
    f"{selected_match['home_score']}–{selected_match['away_score']} "
    f"{selected_match['away_team']}"
)
match_label = f"{score_label} | {selected_row['competition_name']} {selected_row['season_name']}"

if run:
    with st.spinner('Loading match data...'):
        events = data_loader.get_events(match_id)

    figs: list[tuple[str, plt.Figure]] = []
    errors: list[str] = []

    with st.spinner('Drawing visualizations...'):
        for analysis in selected_analyses:
            try:
                if analysis == 'Passing Network':
                    fig = draw_passing_network(events, selected_team, match_label)
                elif analysis == 'Heat Map':
                    if selected_player is None:
                        errors.append('Heat Map: no player selected.')
                        continue
                    fig = draw_heat_map(events, selected_player, selected_team, match_label)
                elif analysis == 'Shot Map':
                    fig = draw_shot_map(events, selected_team, match_label)
                else:
                    fig = draw_press_map(events, selected_team, match_label)
                figs.append((analysis, fig))
            except ValueError as e:
                errors.append(str(e))
            except Exception as e:
                errors.append(f'{analysis}: {e}')

    for err in errors:
        st.error(err)

    if figs:
        try:
            cols = st.columns(len(figs))
            for col, (analysis, fig) in zip(cols, figs):
                with col:
                    st.caption(analysis)
                    st.pyplot(fig)

            n_buttons = len(figs) + (1 if len(figs) > 1 else 0)
            dl_cols = st.columns(n_buttons)

            for i, (analysis, fig) in enumerate(figs):
                buf = io.BytesIO()
                fig.savefig(buf, format='png', dpi=150, bbox_inches='tight')
                buf.seek(0)
                filename = (
                    f"{selected_team.replace(' ', '_').lower()}_"
                    f"{analysis.replace(' ', '_').lower()}.png"
                )
                with dl_cols[i]:
                    st.download_button(
                        label=f'↓ {analysis}',
                        data=buf,
                        file_name=filename,
                        mime='image/png',
                        use_container_width=True,
                    )

            if len(figs) > 1:
                stitched = stitch_figures([fig for _, fig in figs])
                all_filename = f"{selected_team.replace(' ', '_').lower()}_all_analyses.png"
                with dl_cols[-1]:
                    st.download_button(
                        label='↓ Download All',
                        data=stitched,
                        file_name=all_filename,
                        mime='image/png',
                        use_container_width=True,
                    )
        finally:
            for _, fig in figs:
                plt.close(fig)

        # Build stats summary for content generation
        selected_analysis = selected_analyses[0] if selected_analyses else ''
        if selected_analysis == 'Shot Map':
            shots = events[(events['type'] == 'Shot') & (events['team'] == selected_team)]
            goals = shots[shots['shot_outcome'] == 'Goal']
            total_xg = shots['shot_statsbomb_xg'].fillna(0).sum()
            stats_summary = (
                f"Shots: {len(shots)}, Goals: {len(goals)}, "
                f"Total xG: {total_xg:.2f}, xG per shot: {total_xg/max(len(shots),1):.2f}"
            )
        elif selected_analysis == 'Press Map':
            pressure = events[
                (events['type'] == 'Pressure') & (events['team'] == selected_team)
            ]
            stats_summary = f"Total pressures: {len(pressure)}"
        elif selected_analysis == 'Passing Network':
            passes = events[
                (events['type'] == 'Pass') & (events['team'] == selected_team) &
                (events['pass_outcome'].isna())
            ]
            stats_summary = f"Successful passes: {len(passes)}"
        elif selected_analysis == 'Heat Map':
            player_events = events[
                (events['team'] == selected_team) &
                (events['player'] == selected_player) &
                (events['location'].notna())
            ]
            stats_summary = (
                f"Player: {selected_player}, "
                f"Total touch events: {len(player_events)}, "
                f"Event types: {', '.join(player_events['type'].value_counts().head(3).index.tolist())}"
            )
        else:
            stats_summary = 'No stats available'

        st.divider()
        st.subheader('Generate Content')
        st.caption('AI-drafted content in your voice. Edit before publishing.')

        if st.button('Generate Newsletter Draft + Twitter Thread'):
            with st.spinner('Writing content...'):
                try:
                    newsletter, twitter = generate_content(
                        selected_analysis, selected_team,
                        match_label, stats_summary
                    )

                    col1, col2 = st.columns(2)

                    with col1:
                        st.markdown('**Newsletter Draft**')
                        st.text_area(
                            label='newsletter',
                            value=newsletter,
                            height=300,
                            label_visibility='collapsed'
                        )

                    with col2:
                        st.markdown('**Twitter Thread**')
                        st.text_area(
                            label='twitter',
                            value=twitter,
                            height=300,
                            label_visibility='collapsed'
                        )

                except Exception as e:
                    st.error(f'Content generation failed: {e}')

else:
    if not selected_analyses:
        st.warning('Select at least one analysis type from the sidebar.')
    else:
        st.info('Configure your selection in the sidebar and click **Generate Visualization**.')
