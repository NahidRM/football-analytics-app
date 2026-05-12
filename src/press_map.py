# press_map.py
#
# PURPOSE: Generate a press intensity map for Arsenal showing where the team
# applied defensive pressure throughout the match.
#
# WHAT IS A PRESS MAP?
# Every time an Arsenal player closes down an opponent, StatsBomb records it as
# a 'Pressure' event with an x/y location. We collect all those locations and
# use KDE to show which zones of the pitch Arsenal hunted in most.
#
# High density in the opponent's half = high press
# High density in Arsenal's own half = mid/low block
#
# NOTE ON LOCATIONS: The coordinates represent where the Arsenal player was
# when they pressed — not the ball's position. In practice these are very
# close, so the map accurately reflects the team's defensive shape.
#
# HOW TO RUN (with venv active):
#   python3 src/press_map.py

# ── IMPORTS ──────────────────────────────────────────────────────────────────
from statsbombpy import sb
import matplotlib.pyplot as plt
from mplsoccer import Pitch
from matplotlib.colors import LinearSegmentedColormap
import os
import warnings
warnings.filterwarnings('ignore')
from config import CLUB_COLORS, FALLBACK_COLOR, PITCH_COLOR, FIGURE_COLOR, LINE_COLOR, LINE_ALPHA, ACCENT_COLOR, PRESS_COLOR


# ── SETTINGS ─────────────────────────────────────────────────────────────────
MATCH_ID = 3749448
TEAM     = 'Arsenal'

OUTPUT_PATH = f"outputs/{TEAM.replace(' ', '_').lower()}_press_map.png"


# Colors loaded from config.py — edit that file to update all scripts at once
TEAM_COLOR = CLUB_COLORS.get(TEAM, FALLBACK_COLOR)
HEAT_CMAP  = LinearSegmentedColormap.from_list('press_heat', [PITCH_COLOR, PRESS_COLOR])


# ── STEP 1: LOAD MATCH EVENTS ─────────────────────────────────────────────────
print("Loading match events...")
events = sb.events(match_id=MATCH_ID)
print(f"Loaded {len(events)} events\n")


# ── STEP 2: FILTER TO ARSENAL PRESSURE EVENTS ────────────────────────────────
pressure = events[
    (events['type'] == 'Pressure') &
    (events['team'] == TEAM) &
    (events['location'].notna())
].copy()

print(f"Arsenal pressure events: {len(pressure)}")


# ── STEP 3: EXTRACT COORDINATES ──────────────────────────────────────────────
pressure['x'] = pressure['location'].apply(lambda loc: loc[0])
pressure['y'] = pressure['location'].apply(lambda loc: loc[1])

print(f"X range: {pressure['x'].min():.1f} → {pressure['x'].max():.1f}")
print(f"Y range: {pressure['y'].min():.1f} → {pressure['y'].max():.1f}\n")


# ── STEP 4: DRAW THE PRESS MAP ────────────────────────────────────────────────
print("Drawing press map...")

# Horizontal pitch — full pitch so we can see whether Arsenal press high or deep
pitch = Pitch(
    pitch_type='statsbomb',
    pitch_color=PITCH_COLOR,
    line_color=LINE_COLOR,
    line_alpha=LINE_ALPHA
)

fig, ax = pitch.draw(figsize=(14, 9))
fig.patch.set_facecolor(FIGURE_COLOR)

pitch.kdeplot(
    pressure['x'],
    pressure['y'],
    ax=ax,
    shade=True,
    levels=100,
    cmap=HEAT_CMAP,
    alpha=0.75,
    bw_adjust=0.6
)

# ── ZONE ANNOTATIONS ─────────────────────────────────────────────────────────
# Divide the pitch into thirds (StatsBomb x: 0→120) and count presses in each.
# Dashed lines mark the boundaries; counts + percentages label each zone.
THIRD_BOUNDARIES = [40, 80]   # x coordinates dividing defensive / middle / attacking thirds
ZONE_LABELS = ['Defensive\nThird', 'Middle\nThird', 'Attacking\nThird']
ZONE_X_RANGES = [(0, 40), (40, 80), (80, 120)]
ZONE_MIDPOINTS = [20, 60, 100]

total_presses = len(pressure)

for x_boundary in THIRD_BOUNDARIES:
    ax.axvline(
        x=x_boundary,
        color=ACCENT_COLOR,
        linestyle='--',
        linewidth=0.8,
        alpha=0.4
    )

for (x_min, x_max), label, midpoint in zip(ZONE_X_RANGES, ZONE_LABELS, ZONE_MIDPOINTS):
    zone_count = len(pressure[(pressure['x'] >= x_min) & (pressure['x'] < x_max)])
    zone_pct   = zone_count / total_presses * 100

    # Zone label at top
    ax.text(
        midpoint, 72,
        label,
        color=ACCENT_COLOR,
        fontsize=7.5,
        ha='center',
        va='center',
        alpha=0.6
    )

    # Count + percentage just below the label
    ax.text(
        midpoint, 65,
        f'{zone_count} presses\n{zone_pct:.0f}%',
        color=PRESS_COLOR,
        fontsize=9,
        fontweight='bold',
        ha='center',
        va='center'
    )

# ATTACK DIRECTION ARROW
ax.annotate(
    '',
    xy=(110, 76), xytext=(90, 76),
    arrowprops=dict(arrowstyle='->', color=ACCENT_COLOR, lw=1.5)
)
ax.text(100, 78, 'Attacking direction', color=ACCENT_COLOR,
        fontsize=7.5, ha='center', va='bottom', style='italic')

# LEGEND
fig.text(
    0.5, 0.01,
    f'Based on {len(pressure)} pressure events  |  Brighter = higher press intensity',
    color=ACCENT_COLOR,
    fontsize=8.5,
    ha='center',
    va='bottom',
    bbox=dict(
        boxstyle='round,pad=0.5',
        facecolor=PITCH_COLOR,
        alpha=0.9,
        edgecolor=ACCENT_COLOR,
        linewidth=0.8
    )
)

# TITLE
ax.set_title(
    f'{TEAM} Press Intensity Map\n'
    f'Arsenal 4–2 Liverpool  |  Premier League 2003/04',
    color=ACCENT_COLOR,
    fontsize=12,
    fontweight='bold',
    pad=20
)


# ── STEP 5: SAVE ──────────────────────────────────────────────────────────────
os.makedirs('outputs', exist_ok=True)
plt.tight_layout()
plt.savefig(OUTPUT_PATH, dpi=150, bbox_inches='tight', facecolor=FIGURE_COLOR)
plt.close()

print(f"\nDone! Image saved to: {OUTPUT_PATH}")
print("Open that file to see the press map.")
