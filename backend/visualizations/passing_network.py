# passing_network.py
#
# PURPOSE: Generate a passing network visualization.
# Exposes draw_passing_network() for use by the Streamlit app.
# Can also be run directly: python3 src/passing_network.py

import pandas as pd
import matplotlib.pyplot as plt
from mplsoccer import Pitch
import warnings
warnings.filterwarnings('ignore')
from backend.config import (
    CLUB_COLORS, FALLBACK_COLOR, PITCH_COLOR, FIGURE_COLOR,
    LINE_COLOR, LINE_ALPHA, ACCENT_COLOR
)

EDGE_COLOR = '#333333'

# Known StatsBomb name quirks — see LEARNINGS.md for why these exist
DISPLAY_NAME_OVERRIDES = {
    "Sulzeer Jeremiah ''Sol' Campbell": 'Campbell',
    'Laureano Bisan-Etame Mayer':       'Lauren',
    'Kolo Habib Touré':                 'Touré',
    'Gilberto Aparecido da Silva':      'Gilberto',
}


def draw_passing_network(
    events: pd.DataFrame,
    team: str,
    match_label: str,
    display_name_overrides: dict | None = None
) -> plt.Figure:
    """
    Build and return a passing network figure for the given team.

    Args:
        events:                 Full match events DataFrame from StatsBomb.
        team:                   Team name as stored in StatsBomb (e.g. 'Arsenal').
        match_label:            Title line 2 (e.g. 'Arsenal 4-2 Liverpool | Premier League 2003/04').
        display_name_overrides: Optional dict mapping full StatsBomb names to display names.
                                Defaults to the module-level DISPLAY_NAME_OVERRIDES.
    Returns:
        A matplotlib Figure. Caller is responsible for closing it (plt.close(fig)).
    """
    overrides = display_name_overrides if display_name_overrides is not None else DISPLAY_NAME_OVERRIDES
    team_color = CLUB_COLORS.get(team, FALLBACK_COLOR)

    # Starting XI
    lineup_event = events[(events['type'] == 'Starting XI') & (events['team'] == team)]
    tactics = lineup_event.iloc[0]['tactics']
    formation = tactics['formation']
    starting_xi = [p['player']['name'] for p in tactics['lineup']]

    # First substitution
    subs = events[(events['type'] == 'Substitution') & (events['team'] == team)]
    first_sub_minute = subs['minute'].min() if len(subs) > 0 else 90

    # Filter passes
    passes = events[
        (events['type'] == 'Pass') &
        (events['team'] == team) &
        (events['minute'] < first_sub_minute) &
        (events['player'].isin(starting_xi)) &
        (events['pass_recipient'].isin(starting_xi)) &
        (events['pass_outcome'].isna())
    ].copy()

    passes['x']     = passes['location'].apply(lambda loc: loc[0])
    passes['y']     = passes['location'].apply(lambda loc: loc[1])

    avg_positions = passes.groupby('player').agg(
        avg_x=('x', 'mean'),
        avg_y=('y', 'mean'),
        total_passes=('x', 'count')
    ).reset_index()

    pass_combinations = passes.groupby(
        ['player', 'pass_recipient']
    ).size().reset_index(name='count')
    # Filter to edges at or above 75th percentile of pass frequencies
    threshold = pass_combinations['count'].quantile(0.75)
    pass_combinations = pass_combinations[pass_combinations['count'] >= threshold]

    active_players = set(
        pass_combinations['player'].tolist() +
        pass_combinations['pass_recipient'].tolist()
    )
    avg_positions = avg_positions[avg_positions['player'].isin(active_players)]

    pass_combinations = pass_combinations.merge(
        avg_positions[['player', 'avg_x', 'avg_y']].rename(
            columns={'avg_x': 'x_start', 'avg_y': 'y_start'}
        ), on='player'
    )
    pass_combinations = pass_combinations.merge(
        avg_positions[['player', 'avg_x', 'avg_y']].rename(
            columns={'player': 'pass_recipient', 'avg_x': 'x_end', 'avg_y': 'y_end'}
        ), on='pass_recipient'
    )

    # Draw
    pitch = Pitch(pitch_type='statsbomb', pitch_color=PITCH_COLOR,
                  line_color=LINE_COLOR, line_alpha=LINE_ALPHA)
    fig, ax = pitch.draw(figsize=(14, 9))
    fig.patch.set_facecolor(FIGURE_COLOR)

    max_count = pass_combinations['count'].max()
    for _, row in pass_combinations.iterrows():
        pitch.lines(
            row['x_start'], row['y_start'], row['x_end'], row['y_end'],
            lw=1 + (row['count'] / max_count) * 9,
            color=EDGE_COLOR,
            alpha=0.2 + (row['count'] / max_count) * 0.6,
            ax=ax, zorder=1
        )

    max_passes = avg_positions['total_passes'].max()
    for _, row in avg_positions.iterrows():
        node_size = 300 + (row['total_passes'] / max_passes) * 700
        pitch.scatter(row['avg_x'], row['avg_y'], s=node_size, color=team_color,
                      edgecolors='white', linewidth=2, ax=ax, zorder=2)

        parts = row['player'].split()
        display_name = overrides.get(
            row['player'],
            parts[-1] if len(parts) <= 2 else parts[0]
        )
        ax.annotate(
            display_name, xy=(row['avg_x'], row['avg_y']),
            fontsize=10, color=ACCENT_COLOR, fontweight='bold',
            ha='center', va='bottom', xytext=(0, 12),
            textcoords='offset points', zorder=3,
            bbox=dict(boxstyle='round,pad=0.2', facecolor=PITCH_COLOR,
                      alpha=0.6, edgecolor='none')
        )

    ax.annotate('', xy=(110, 76), xytext=(90, 76),
                arrowprops=dict(arrowstyle='->', color=ACCENT_COLOR, lw=1.5))
    ax.text(100, 78, 'Attacking direction', color=ACCENT_COLOR,
            fontsize=7.5, ha='center', va='bottom', style='italic')

    fig.text(0.5, 0.01,
             '● Node size = passes made          ─  Line width = pass frequency',
             color=ACCENT_COLOR, fontsize=8.5, ha='center', va='bottom',
             bbox=dict(boxstyle='round,pad=0.5', facecolor=PITCH_COLOR,
                       alpha=0.9, edgecolor=ACCENT_COLOR, linewidth=0.8))

    ax.set_title(
        f'{team} Passing Network\n{match_label}\n'
        f'Formation: {formation}  |  Starting XI only, before first substitution',
        color=ACCENT_COLOR, fontsize=12, fontweight='bold', pad=20
    )

    return fig


if __name__ == '__main__':
    import os
    from statsbombpy import sb
    events = sb.events(match_id=3749448)
    fig = draw_passing_network(events, 'Arsenal', 'Arsenal 4–2 Liverpool | Premier League 2003/04')
    os.makedirs('outputs', exist_ok=True)
    fig.savefig('outputs/arsenal_passing_network.png', dpi=150, bbox_inches='tight',
                facecolor=FIGURE_COLOR)
    plt.close(fig)
    print("Done! Image saved to outputs/arsenal_passing_network.png")
