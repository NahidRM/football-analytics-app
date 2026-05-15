# press_map.py
#
# PURPOSE: Generate a press intensity heat map.
# Exposes draw_press_map() for use by the Streamlit app.
# Can also be run directly: python3 src/press_map.py

import pandas as pd
import matplotlib.pyplot as plt
from mplsoccer import Pitch
from matplotlib.colors import LinearSegmentedColormap
import warnings
warnings.filterwarnings('ignore')
from backend.config import (
    PITCH_COLOR, FIGURE_COLOR, LINE_COLOR, LINE_ALPHA, ACCENT_COLOR, PRESS_COLOR
)

THIRD_BOUNDARIES = [40, 80]
ZONE_LABELS      = ['Defensive\nThird', 'Middle\nThird', 'Attacking\nThird']
ZONE_X_RANGES    = [(0, 40), (40, 80), (80, 120)]
ZONE_MIDPOINTS   = [20, 60, 100]


def draw_press_map(
    events: pd.DataFrame,
    team: str,
    match_label: str
) -> plt.Figure:
    """
    Build and return a press intensity map figure for the given team.

    Args:
        events:       Full match events DataFrame from StatsBomb.
        team:         Team name as stored in StatsBomb.
        match_label:  Title line 2 (e.g. 'Arsenal 4-2 Liverpool | Premier League 2003/04').
    Returns:
        A matplotlib Figure. Caller is responsible for closing it (plt.close(fig)).
    """
    heat_cmap = LinearSegmentedColormap.from_list('press_heat', [PITCH_COLOR, PRESS_COLOR])

    pressure = events[
        (events['type'] == 'Pressure') &
        (events['team'] == team) &
        (events['location'].notna())
    ].copy()

    pressure['x'] = pressure['location'].apply(lambda loc: loc[0])
    pressure['y'] = pressure['location'].apply(lambda loc: loc[1])

    pitch = Pitch(pitch_type='statsbomb', pitch_color=PITCH_COLOR,
                  line_color=LINE_COLOR, line_alpha=LINE_ALPHA)
    fig, ax = pitch.draw(figsize=(14, 9))
    fig.patch.set_facecolor(FIGURE_COLOR)

    pitch.kdeplot(
        pressure['x'], pressure['y'],
        ax=ax, shade=True, levels=100,
        cmap=heat_cmap, alpha=0.75, bw_adjust=0.6
    )

    total_presses = len(pressure)
    for x_boundary in THIRD_BOUNDARIES:
        ax.axvline(x=x_boundary, color=ACCENT_COLOR, linestyle='--',
                   linewidth=0.8, alpha=0.4)

    for (x_min, x_max), label, midpoint in zip(ZONE_X_RANGES, ZONE_LABELS, ZONE_MIDPOINTS):
        zone_count = len(pressure[(pressure['x'] >= x_min) & (pressure['x'] < x_max)])
        zone_pct   = zone_count / total_presses * 100
        ax.text(midpoint, 72, label, color=ACCENT_COLOR, fontsize=7.5,
                ha='center', va='center', alpha=0.6)
        ax.text(midpoint, 65, f'{zone_count} presses\n{zone_pct:.0f}%',
                color=PRESS_COLOR, fontsize=9, fontweight='bold',
                ha='center', va='center')

    ax.annotate('', xy=(110, 76), xytext=(90, 76),
                arrowprops=dict(arrowstyle='->', color=ACCENT_COLOR, lw=1.5))
    ax.text(100, 78, 'Attacking direction', color=ACCENT_COLOR,
            fontsize=7.5, ha='center', va='bottom', style='italic')

    fig.text(
        0.5, 0.01,
        f'Based on {total_presses} pressure events  |  Brighter = higher press intensity',
        color=ACCENT_COLOR, fontsize=8.5, ha='center', va='bottom',
        bbox=dict(boxstyle='round,pad=0.5', facecolor=PITCH_COLOR,
                  alpha=0.9, edgecolor=ACCENT_COLOR, linewidth=0.8)
    )

    ax.set_title(
        f'{team} Press Intensity Map\n{match_label}',
        color=ACCENT_COLOR, fontsize=12, fontweight='bold', pad=20
    )

    return fig


if __name__ == '__main__':
    import os
    from statsbombpy import sb
    events = sb.events(match_id=3749448)
    fig = draw_press_map(events, 'Arsenal', 'Arsenal 4–2 Liverpool | Premier League 2003/04')
    os.makedirs('outputs', exist_ok=True)
    fig.savefig('outputs/arsenal_press_map.png', dpi=150, bbox_inches='tight',
                facecolor=FIGURE_COLOR)
    plt.close(fig)
    print("Done! Image saved to outputs/arsenal_press_map.png")
