# heat_map.py
#
# PURPOSE: Generate a touch heat map for a chosen player using KDE (Kernel Density
# Estimation) — showing where on the pitch they spent most of their time.
#
# WHAT IS A HEAT MAP?
# Every time a player touches the ball (pass, shot, carry, receipt, etc.) StatsBomb
# records the x/y location. We collect all those locations and use KDE to smooth them
# into a colour gradient — brighter/warmer = more time spent there.
#
# HOW TO RUN (with venv active):
#   python3 src/heat_map.py

# ── IMPORTS ──────────────────────────────────────────────────────────────────
from statsbombpy import sb
import pandas as pd
import matplotlib.pyplot as plt
from mplsoccer import Pitch
from matplotlib.colors import LinearSegmentedColormap
import os
import warnings
warnings.filterwarnings('ignore')
from config import CLUB_COLORS, FALLBACK_COLOR, PITCH_COLOR, FIGURE_COLOR, LINE_COLOR, LINE_ALPHA, ACCENT_COLOR


# ── SETTINGS ─────────────────────────────────────────────────────────────────
# Change PLAYER_NAME to any player from the match to get their heat map.
# The name must match StatsBomb's spelling exactly — run explore_data.py and
# look at the 'player' column if you're unsure of the exact name.
MATCH_ID    = 3749448
TEAM        = 'Arsenal'
PLAYER_NAME = 'Thierry Henry'

OUTPUT_PATH = f"outputs/{PLAYER_NAME.replace(' ', '_').lower()}_heat_map.png"


# Colors loaded from config.py — edit that file to update all scripts at once
TEAM_COLOR = CLUB_COLORS.get(TEAM, FALLBACK_COLOR)

# ── HEAT MAP COLORMAP ─────────────────────────────────────────────────────────
# Gradient runs from the pitch color (low density — blends in) to the team's
# primary color (high density — pops). Ties the heat map to the club visually.
HEAT_CMAP = LinearSegmentedColormap.from_list(
    'team_heat', [PITCH_COLOR, TEAM_COLOR]
)


# ── STEP 1: LOAD MATCH EVENTS ─────────────────────────────────────────────────
print("Loading match events...")
events = sb.events(match_id=MATCH_ID)
print(f"Loaded {len(events)} events\n")


# ── STEP 2: FILTER TO THIS PLAYER'S TOUCHES ──────────────────────────────────
# We want every event where this player was involved AND a location was recorded.
# StatsBomb records a 'location' for most action types (passes, shots, carries,
# ball receipts, etc.) — this gives us the fullest picture of where they operated.
#
# Some events (e.g. match start, substitution) have no location — we drop those.
player_events = events[
    (events['team'] == TEAM) &
    (events['player'] == PLAYER_NAME) &
    (events['location'].notna())
].copy()

if len(player_events) == 0:
    print(f"No events found for '{PLAYER_NAME}'. Check the name matches StatsBomb exactly.")
    print("Tip: run explore_data.py and inspect the 'player' column.")
    exit()

print(f"Found {len(player_events)} touch events for {PLAYER_NAME}")
print(f"Event types included: {player_events['type'].value_counts().to_dict()}\n")


# ── STEP 3: EXTRACT X/Y COORDINATES ──────────────────────────────────────────
# Each 'location' is a list: [x, y]
# StatsBomb pitch: x goes 0→120 (left to right), y goes 0→80 (bottom to top)
player_events['x'] = player_events['location'].apply(lambda loc: loc[0])
player_events['y'] = player_events['location'].apply(lambda loc: loc[1])

print(f"X range: {player_events['x'].min():.1f} → {player_events['x'].max():.1f}")
print(f"Y range: {player_events['y'].min():.1f} → {player_events['y'].max():.1f}\n")


# ── STEP 4: DRAW THE HEAT MAP ─────────────────────────────────────────────────
print("Drawing heat map...")

pitch = Pitch(
    pitch_type='statsbomb',
    pitch_color=PITCH_COLOR,
    line_color=LINE_COLOR,
    line_alpha=LINE_ALPHA
)

fig, ax = pitch.draw(figsize=(14, 9))
fig.patch.set_facecolor(FIGURE_COLOR)

# pitch.kdeplot() is mplsoccer's built-in KDE heat map method.
# It takes the x/y coordinates and handles all the density maths internally.
#
# Key parameters:
#   shade=True       — fills the area under the density curve with colour
#   levels=100       — how many colour bands to draw (more = smoother gradient)
#   cmap             — the colour map (palette). 'hot' goes black → red → yellow → white
#   alpha            — transparency of the overlay so pitch lines show through
pitch.kdeplot(
    player_events['x'],
    player_events['y'],
    ax=ax,
    shade=True,
    levels=100,
    cmap=HEAT_CMAP,
    alpha=0.65,
    bw_adjust=0.6   # tighter kernel — focuses on genuinely dense zones, reduces spread
)

# ATTACK DIRECTION ARROW — same as passing network
ax.annotate(
    '',
    xy=(110, 76), xytext=(90, 76),
    arrowprops=dict(arrowstyle='->', color=ACCENT_COLOR, lw=1.5)
)
ax.text(100, 78, 'Attacking direction', color=ACCENT_COLOR,
        fontsize=7.5, ha='center', va='bottom', style='italic')

# TOUCH COUNT — useful context shown in the legend
fig.text(
    0.5, 0.01,
    f'Based on {len(player_events)} touch events  |  Brighter = more time spent in that zone',
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
    f'{PLAYER_NAME} — Touch Heat Map\n'
    f'Arsenal 4–2 Liverpool  |  Premier League 2003/04',
    color=ACCENT_COLOR,
    fontsize=12,
    fontweight='bold',
    pad=20
)


# ── STEP 5: SAVE THE IMAGE ────────────────────────────────────────────────────
os.makedirs('outputs', exist_ok=True)
plt.tight_layout()
plt.savefig(OUTPUT_PATH, dpi=150, bbox_inches='tight', facecolor=FIGURE_COLOR)
plt.close()

print(f"\nDone! Image saved to: {OUTPUT_PATH}")
print("Open that file to see the heat map.")
