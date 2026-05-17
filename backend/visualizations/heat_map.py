# heat_map.py
#
# PURPOSE: Generate a touch heat map for a player.
# Exposes draw_heat_map() for use by the Streamlit app.
# Can also be run directly: python3 src/heat_map.py

import pandas as pd
import matplotlib.pyplot as plt
from mplsoccer import Pitch
from matplotlib.colors import LinearSegmentedColormap
import warnings
warnings.filterwarnings('ignore')
from backend.config import (
    CLUB_COLORS, FALLBACK_COLOR, PITCH_COLOR, FIGURE_COLOR,
    LINE_COLOR, LINE_ALPHA, ACCENT_COLOR
)


def draw_heat_map(
    events: pd.DataFrame,
    player_name: str,
    team: str,
    match_label: str
) -> plt.Figure:
    """
    Build and return a heat map figure for a single player.

    Args:
        events:       Full match events DataFrame from StatsBomb.
        player_name:  Player name exactly as stored in StatsBomb.
        team:         Team name (used to validate the player is on the right team).
        match_label:  Title line 2 (e.g. 'Arsenal 4-2 Liverpool | Premier League 2003/04').
    Returns:
        A matplotlib Figure. Caller is responsible for closing it (plt.close(fig)).
    Raises:
        ValueError: if no touch events are found for this player+team combination.
    """
    team_color = CLUB_COLORS.get(team, FALLBACK_COLOR)
    heat_cmap = LinearSegmentedColormap.from_list('team_heat', [PITCH_COLOR, team_color])

    player_events = events[
        (events['team'] == team) &
        (events['player'] == player_name) &
        (events['location'].notna())
    ].copy()

    if len(player_events) == 0:
        raise ValueError(
            f"No touch events found for '{player_name}' on '{team}'. "
            "Check the name matches StatsBomb exactly."
        )

    player_events['x'] = player_events['location'].apply(lambda loc: loc[0])
    player_events['y'] = player_events['location'].apply(lambda loc: loc[1])

    pitch = Pitch(pitch_type='statsbomb', pitch_color=PITCH_COLOR,
                  line_color=LINE_COLOR, line_alpha=LINE_ALPHA)
    fig, ax = pitch.draw(figsize=(14, 9))
    fig.patch.set_facecolor(FIGURE_COLOR)

    pitch.kdeplot(
        player_events['x'], player_events['y'],
        ax=ax, shade=True, levels=100,
        cmap=heat_cmap, alpha=0.65, bw_adjust=0.6
    )

    ax.annotate('', xy=(110, 76), xytext=(90, 76),
                arrowprops=dict(arrowstyle='->', color=ACCENT_COLOR, lw=1.5))
    ax.text(100, 78, 'Attacking direction', color=ACCENT_COLOR,
            fontsize=7.5, ha='center', va='bottom', style='italic')

    fig.text(
        0.5, 0.01,
        f'Based on {len(player_events)} touch events  |  Brighter = more time spent in that zone',
        color=ACCENT_COLOR, fontsize=8.5, ha='center', va='bottom',
        bbox=dict(boxstyle='round,pad=0.5', facecolor=PITCH_COLOR,
                  alpha=0.9, edgecolor=ACCENT_COLOR, linewidth=0.8)
    )

    ax.set_title(
        f'{player_name} — Touch Heat Map\n{match_label}',
        color=ACCENT_COLOR, fontsize=12, fontweight='bold', pad=20
    )

    return fig


if __name__ == '__main__':
    import os
    from statsbombpy import sb
    events = sb.events(match_id=3749448)
    fig = draw_heat_map(events, 'Thierry Henry', 'Arsenal',
                        'Arsenal 4–2 Liverpool | Premier League 2003/04')
    os.makedirs('outputs', exist_ok=True)
    fig.savefig('outputs/thierry_henry_heat_map.png', dpi=150, bbox_inches='tight',
                facecolor=FIGURE_COLOR)
    plt.close(fig)
    print("Done! Image saved to outputs/thierry_henry_heat_map.png")
