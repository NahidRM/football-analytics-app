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
    page_title='The Whiteboard',
    layout='wide'
)

st.markdown("""
<style>
    header[data-testid="stHeader"] { display: none !important; }
    [data-testid="stStatusWidget"] { display: none !important; }
    #MainMenu { display: none !important; }
    footer { display: none !important; }
</style>
""", unsafe_allow_html=True)

st.title('The Whiteboard')


def _request_content_generation():
    """Callback: flag that the user wants content generated on the next rerun."""
    st.session_state['generate_content_requested'] = True


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

            # Store viz bytes in session state so it can be shown alongside generated content
            if len(figs) > 1:
                st.session_state['viz_bytes'] = stitch_figures([fig for _, fig in figs])
            else:
                _vbuf = io.BytesIO()
                figs[0][1].savefig(_vbuf, format='png', dpi=150, bbox_inches='tight')
                _vbuf.seek(0)
                st.session_state['viz_bytes'] = _vbuf.read()

        finally:
            for _, fig in figs:
                plt.close(fig)

        # Build richer stats summary for content generation
        selected_analysis = selected_analyses[0] if selected_analyses else ''

        def _loc_x(loc):
            return loc[0] if isinstance(loc, list) and len(loc) >= 2 else None

        def _loc_y(loc):
            return loc[1] if isinstance(loc, list) and len(loc) >= 2 else None

        if selected_analysis == 'Passing Network':
            passes = events[
                (events['type'] == 'Pass') & (events['team'] == selected_team) &
                (events['pass_outcome'].isna())
            ]
            pairs_info = ''
            if 'pass_recipient' in passes.columns and not passes.empty:
                pairs = passes.groupby(['player', 'pass_recipient']).size().reset_index(name='count')
                top = pairs.nlargest(3, 'count')
                pairs_list = [
                    f"{r['player'].split()[-1]} → {r['pass_recipient'].split()[-1]} ({r['count']})"
                    for _, r in top.iterrows()
                ]
                pairs_info = f"Top passing pairs: {', '.join(pairs_list)}. "

            connections = passes['player'].value_counts()
            most_conn = connections.index[0] if not connections.empty else 'Unknown'
            least_conn = connections.index[-1] if not connections.empty else 'Unknown'

            pos_info = ''
            if 'location' in passes.columns and not passes.empty:
                locs = passes['location'].dropna()
                xs = locs.apply(_loc_x).dropna()
                ys = locs.apply(_loc_y).dropna()
                if not xs.empty:
                    avg_x, avg_y = xs.mean(), ys.mean()
                    depth = 'in their own half' if avg_x < 60 else 'in the opposition half'
                    side = 'left-side dominant' if avg_y < 33 else 'right-side dominant' if avg_y > 47 else 'centrally dominant'
                    pos_info = f"Build-up play was {depth} and {side}. "

            stats_summary = (
                f"Successful passes: {len(passes)}. "
                f"{pairs_info}"
                f"Most active passer: {most_conn}. Least involved: {least_conn}. "
                f"{pos_info}"
            )

        elif selected_analysis == 'Shot Map':
            shots = events[(events['type'] == 'Shot') & (events['team'] == selected_team)]
            goals = shots[shots['shot_outcome'] == 'Goal']
            total_xg = shots['shot_statsbomb_xg'].fillna(0).sum()
            on_target = shots[shots['shot_outcome'].isin(['Goal', 'Saved'])]

            zone_info = ''
            if 'location' in shots.columns and not shots.empty:
                s_loc = shots[shots['location'].notna()].copy()
                s_loc['x'] = s_loc['location'].apply(_loc_x)
                inside_box = s_loc[s_loc['x'] >= 102]
                zone_info = (
                    f"Shots inside penalty box: {len(inside_box)}, "
                    f"outside: {len(s_loc) - len(inside_box)}. "
                )

            best_info = ''
            if not shots.empty and 'shot_statsbomb_xg' in shots.columns:
                best = shots.loc[shots['shot_statsbomb_xg'].fillna(0).idxmax()]
                best_info = (
                    f"Highest xG chance: {best.get('player', 'Unknown')} "
                    f"({best.get('shot_statsbomb_xg', 0):.2f} xG, "
                    f"outcome: {best.get('shot_outcome', 'Unknown')}). "
                )

            stats_summary = (
                f"Shots: {len(shots)}, Goals: {len(goals)}, On target: {len(on_target)}, "
                f"Total xG: {total_xg:.2f}, xG per shot: {total_xg/max(len(shots),1):.2f}. "
                f"{zone_info}{best_info}"
            )

        elif selected_analysis == 'Press Map':
            pressure = events[
                (events['type'] == 'Pressure') & (events['team'] == selected_team)
            ]
            zone_info = ''
            if 'location' in pressure.columns and not pressure.empty:
                p_loc = pressure[pressure['location'].notna()].copy()
                p_loc['x'] = p_loc['location'].apply(_loc_x)
                p_loc = p_loc.dropna(subset=['x'])
                if not p_loc.empty:
                    def_t = len(p_loc[p_loc['x'] < 40])
                    mid_t = len(p_loc[(p_loc['x'] >= 40) & (p_loc['x'] < 80)])
                    att_t = len(p_loc[p_loc['x'] >= 80])
                    total = len(p_loc)
                    top_third = max([('defensive', def_t), ('middle', mid_t), ('attacking', att_t)], key=lambda v: v[1])[0]
                    zone_info = (
                        f"By third — defensive: {def_t} ({100*def_t//max(total,1)}%), "
                        f"middle: {mid_t} ({100*mid_t//max(total,1)}%), "
                        f"attacking: {att_t} ({100*att_t//max(total,1)}%). "
                        f"Most pressing in the {top_third} third."
                    )
            stats_summary = f"Total pressures: {len(pressure)}. {zone_info}"

        elif selected_analysis == 'Heat Map':
            player_events = events[
                (events['team'] == selected_team) &
                (events['player'] == selected_player) &
                (events['location'].notna())
            ]
            if player_events.empty:
                stats_summary = f"Player: {selected_player}, No touch events found"
            else:
                top_types = ', '.join(player_events['type'].value_counts().head(3).index.tolist())
                pos_info = ''
                p_ev = player_events.copy()
                p_ev['x'] = p_ev['location'].apply(_loc_x)
                p_ev['y'] = p_ev['location'].apply(_loc_y)
                p_ev = p_ev.dropna(subset=['x', 'y'])
                if not p_ev.empty:
                    avg_x, avg_y = p_ev['x'].mean(), p_ev['y'].mean()
                    side = 'left flank' if avg_y < 27 else 'right flank' if avg_y > 53 else 'central areas'
                    depth = 'deep in his own half' if avg_x < 50 else 'high up the pitch' if avg_x > 70 else 'in midfield'
                    pos_info = f"Average position: {side}, {depth}. "
                stats_summary = (
                    f"Player: {selected_player}, "
                    f"Total touch events: {len(player_events)}, "
                    f"Primary actions: {top_types}. "
                    f"{pos_info}"
                )

        else:
            stats_summary = 'No stats available'

        st.session_state['content_context'] = {
            'selected_analysis': selected_analysis,
            'selected_team': selected_team,
            'match_label': match_label,
            'stats_summary': stats_summary,
        }
        st.session_state.pop('generated_newsletter', None)
        st.session_state.pop('generated_twitter', None)

        st.divider()
        st.subheader('Generate Content')
        st.caption('AI-drafted content in your voice. Edit before publishing.')
        st.button(
            'Generate Newsletter Draft + Twitter Thread',
            on_click=_request_content_generation,
        )

else:
    if not selected_analyses:
        st.warning('Select at least one analysis type from the sidebar.')
    else:
        st.info('Configure your selection in the sidebar and click **Generate Visualization**.')

# Generate content if the button was clicked (callback sets this flag before rerun)
if st.session_state.pop('generate_content_requested', False):
    ctx = st.session_state.get('content_context', {})
    with st.spinner('Writing content...'):
        try:
            newsletter, twitter = generate_content(
                ctx['selected_analysis'], ctx['selected_team'],
                ctx['match_label'], ctx['stats_summary']
            )
            st.session_state['generated_newsletter'] = newsletter
            st.session_state['generated_twitter'] = twitter
        except Exception as e:
            st.error(f'Content generation failed: {e}')

# Show generated content (persists across reruns via session state)
if 'generated_newsletter' in st.session_state:
    ctx = st.session_state.get('content_context', {})
    st.divider()
    st.subheader('Generated Content')
    st.caption(
        f"Based on: {ctx.get('selected_analysis', '')} — "
        f"{ctx.get('selected_team', '')} | {ctx.get('match_label', '')}"
    )
    if 'viz_bytes' in st.session_state:
        with st.expander('View Visualization'):
            st.image(st.session_state['viz_bytes'])
    newsletter_tab, twitter_tab = st.tabs(['Newsletter Draft', 'Twitter Thread'])
    with newsletter_tab:
        st.text_area(
            label='newsletter',
            value=st.session_state['generated_newsletter'],
            height=400,
            label_visibility='collapsed',
            key='newsletter_draft'
        )
    with twitter_tab:
        st.text_area(
            label='twitter',
            value=st.session_state['generated_twitter'],
            height=400,
            label_visibility='collapsed',
            key='twitter_draft'
        )
