# shot_map.py
#
# PURPOSE: Generate a shot map for Arsenal showing every shot taken, sized by
# xG (expected goals), with goals clearly marked.
#
# WHAT IS xG?
# Expected Goals (xG) is a probability value between 0 and 1 that represents
# how likely a shot was to result in a goal, based on factors like distance,
# angle, and how the chance was created. A shot with xG 0.9 was a near-certain
# goal; xG 0.05 was a low-quality chance.
#
# WHAT DOES THIS MAP SHOW?
# Each shot is a dot at the location it was taken. Bigger dot = higher xG.
# Goals are highlighted with a white ring so they immediately stand out.
# This lets you see at a glance: where did Arsenal shoot from, how good were
# those chances, and which ones went in?
#
# HOW TO RUN (with venv active):
#   python3 src/shot_map.py

# ── IMPORTS ──────────────────────────────────────────────────────────────────
from statsbombpy import sb
import pandas as pd
import matplotlib.pyplot as plt
from mplsoccer import VerticalPitch
import os
import warnings
warnings.filterwarnings('ignore')
from config import CLUB_COLORS, FALLBACK_COLOR, PITCH_COLOR, FIGURE_COLOR, LINE_COLOR, LINE_ALPHA, ACCENT_COLOR, GOAL_COLOR


# ── SETTINGS ─────────────────────────────────────────────────────────────────
MATCH_ID = 3749448
TEAM     = 'Arsenal'

OUTPUT_PATH = f"outputs/{TEAM.replace(' ', '_').lower()}_shot_map.png"


# Colors loaded from config.py — edit that file to update all scripts at once
TEAM_COLOR = CLUB_COLORS.get(TEAM, FALLBACK_COLOR)


# ── STEP 1: LOAD MATCH EVENTS ─────────────────────────────────────────────────
print("Loading match events...")
events = sb.events(match_id=MATCH_ID)
print(f"Loaded {len(events)} events\n")


# ── STEP 2: FILTER TO ARSENAL SHOTS ──────────────────────────────────────────
shots = events[
    (events['type'] == 'Shot') &
    (events['team'] == TEAM)
].copy()

print(f"Arsenal shots: {len(shots)}")
print(shots[['player', 'minute', 'shot_outcome', 'shot_statsbomb_xg']].to_string(index=False))
print()


# ── STEP 3: EXTRACT COORDINATES AND OUTCOME ──────────────────────────────────
shots['x']    = shots['location'].apply(lambda loc: loc[0])
shots['y']    = shots['location'].apply(lambda loc: loc[1])
shots['goal'] = shots['shot_outcome'] == 'Goal'

# Replace NaN xG with 0 just in case (shouldn't happen with StatsBomb data)
shots['shot_statsbomb_xg'] = shots['shot_statsbomb_xg'].fillna(0)


# ── STEP 4: DRAW THE SHOT MAP ─────────────────────────────────────────────────
# We use VerticalPitch so the attacking direction goes upward — this is the
# standard orientation for shot maps, making the goal mouth immediately obvious
# at the top of the image.
print("Drawing shot map...")

pitch = VerticalPitch(
    pitch_type='statsbomb',
    pitch_color=PITCH_COLOR,
    line_color=LINE_COLOR,
    line_alpha=0.6,
    half=True          # show only the attacking half — all shots happen here
)

fig, ax = pitch.draw(figsize=(10, 10))
fig.patch.set_facecolor(FIGURE_COLOR)

# Separate goals from non-goals for layered drawing
non_goals = shots[~shots['goal']]
goals     = shots[shots['goal']]

# NON-GOALS — semi-transparent, team color
# Node size scales with xG so bigger dot = better chance
pitch.scatter(
    non_goals['x'], non_goals['y'],
    s=non_goals['shot_statsbomb_xg'] * 1500 + 100,   # scale: min 100, max ~1600
    color=TEAM_COLOR,
    alpha=0.4,
    edgecolors=TEAM_COLOR,
    linewidth=1,
    ax=ax,
    zorder=2
)

# GOALS — gold fill with a dark ring so they immediately stand out
pitch.scatter(
    goals['x'], goals['y'],
    s=goals['shot_statsbomb_xg'] * 1500 + 100,
    color=GOAL_COLOR,
    alpha=1.0,
    edgecolors=ACCENT_COLOR,
    linewidth=1.5,
    ax=ax,
    zorder=3
)

# LABEL GOALS with scorer name and minute
for _, row in goals.iterrows():
    # Get surname using the same logic as passing_network.py
    parts = row['player'].split()
    name  = parts[-1] if len(parts) <= 2 else parts[0]

    ax.annotate(
        f"{name} {int(row['minute'])}'",
        xy=(row['x'], row['y']),
        fontsize=8,
        color=ACCENT_COLOR,
        fontweight='bold',
        ha='center',
        va='bottom',
        xytext=(0, 10),
        textcoords='offset points',
        zorder=4
    )


# ── STEP 5: LEGEND AND TITLE ──────────────────────────────────────────────────
# xG summary for the legend
total_xg   = shots['shot_statsbomb_xg'].sum()
total_goals = shots['goal'].sum()

fig.text(
    0.5, 0.01,
    f'Shots: {len(shots)}   |   Goals: {int(total_goals)}   |   Total xG: {total_xg:.2f}'
    f'   |   ● Size = xG   |   ⬤ Green = Goal',
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

ax.set_title(
    f'{TEAM} Shot Map\n'
    f'Arsenal 4–2 Liverpool  |  Premier League 2003/04',
    color=ACCENT_COLOR,
    fontsize=12,
    fontweight='bold',
    pad=20
)


# ── STEP 6: SAVE ──────────────────────────────────────────────────────────────
os.makedirs('outputs', exist_ok=True)
plt.tight_layout()
plt.savefig(OUTPUT_PATH, dpi=150, bbox_inches='tight', facecolor=FIGURE_COLOR)
plt.close()

print(f"\nDone! Image saved to: {OUTPUT_PATH}")
print("Open that file to see the shot map.")
