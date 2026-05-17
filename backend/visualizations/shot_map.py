# shot_map.py
#
# PURPOSE: Generate a shot map with xG sizing.
# Exposes draw_shot_map() for use by the Streamlit app.
# Can also be run directly: python3 src/shot_map.py

import pandas as pd
import matplotlib.pyplot as plt
from mplsoccer import VerticalPitch
import warnings
warnings.filterwarnings('ignore')
from backend.config import (
    CLUB_COLORS, FALLBACK_COLOR, PITCH_COLOR, FIGURE_COLOR,
    LINE_COLOR, ACCENT_COLOR, GOAL_COLOR
)


def draw_shot_map(
    events: pd.DataFrame,
    team: str,
    match_label: str
) -> plt.Figure:
    """
    Build and return a shot map figure for the given team.

    Args:
        events:       Full match events DataFrame from StatsBomb.
        team:         Team name as stored in StatsBomb.
        match_label:  Title line 2 (e.g. 'Arsenal 4-2 Liverpool | Premier League 2003/04').
    Returns:
        A matplotlib Figure. Caller is responsible for closing it (plt.close(fig)).
    """
    team_color = CLUB_COLORS.get(team, FALLBACK_COLOR)

    shots = events[(events['type'] == 'Shot') & (events['team'] == team)].copy()
    shots['x']    = shots['location'].apply(lambda loc: loc[0])
    shots['y']    = shots['location'].apply(lambda loc: loc[1])
    shots['goal'] = shots['shot_outcome'] == 'Goal'
    shots['shot_statsbomb_xg'] = shots['shot_statsbomb_xg'].fillna(0)

    pitch = VerticalPitch(
        pitch_type='statsbomb', pitch_color=PITCH_COLOR,
        line_color=LINE_COLOR, line_alpha=0.6, half=True
    )
    fig, ax = pitch.draw(figsize=(10, 10))
    fig.patch.set_facecolor(FIGURE_COLOR)

    non_goals = shots[~shots['goal']]
    goals     = shots[shots['goal']]

    pitch.scatter(
        non_goals['x'], non_goals['y'],
        s=non_goals['shot_statsbomb_xg'] * 1500 + 100,
        color=team_color, alpha=0.4, edgecolors=team_color, linewidth=1,
        ax=ax, zorder=2
    )
    pitch.scatter(
        goals['x'], goals['y'],
        s=goals['shot_statsbomb_xg'] * 1500 + 100,
        color=GOAL_COLOR, alpha=1.0, edgecolors=ACCENT_COLOR, linewidth=1.5,
        ax=ax, zorder=3
    )

    for _, row in goals.iterrows():
        parts = row['player'].split()
        name  = parts[-1] if len(parts) <= 2 else parts[0]
        ax.annotate(
            f"{name} {int(row['minute'])}'",
            xy=(row['x'], row['y']), fontsize=8, color=ACCENT_COLOR,
            fontweight='bold', ha='center', va='bottom',
            xytext=(0, 10), textcoords='offset points', zorder=4
        )

    total_xg    = shots['shot_statsbomb_xg'].sum()
    total_goals = shots['goal'].sum()

    fig.text(
        0.5, 0.01,
        f'Shots: {len(shots)}   |   Goals: {int(total_goals)}   |   '
        f'Total xG: {total_xg:.2f}   |   ● Size = xG   |   ⬤ Green = Goal',
        color=ACCENT_COLOR, fontsize=8.5, ha='center', va='bottom',
        bbox=dict(boxstyle='round,pad=0.5', facecolor=PITCH_COLOR,
                  alpha=0.9, edgecolor=ACCENT_COLOR, linewidth=0.8)
    )

    ax.set_title(
        f'{team} Shot Map\n{match_label}',
        color=ACCENT_COLOR, fontsize=12, fontweight='bold', pad=20
    )

    return fig


if __name__ == '__main__':
    import os
    from statsbombpy import sb
    events = sb.events(match_id=3749448)
    fig = draw_shot_map(events, 'Arsenal', 'Arsenal 4–2 Liverpool | Premier League 2003/04')
    os.makedirs('outputs', exist_ok=True)
    fig.savefig('outputs/arsenal_shot_map.png', dpi=150, bbox_inches='tight',
                facecolor=FIGURE_COLOR)
    plt.close(fig)
    print("Done! Image saved to outputs/arsenal_shot_map.png")
