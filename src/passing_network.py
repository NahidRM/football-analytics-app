# passing_network.py
#
# PURPOSE: Generate a passing network for Arsenal from the 4-2 win vs Liverpool
# (Premier League 2003/04, match ID 3749448)
#
# WHAT IS A PASSING NETWORK?
# Each player is shown as a dot, positioned at their average location on the pitch.
# Lines connect players who passed to each other — thicker lines mean more passes.
# This reveals the team's shape, key connectors, and how the team is structured
# in possession.
#
# HOW TO RUN (with venv active):
#   python3 src/passing_network.py

# ── IMPORTS ──────────────────────────────────────────────────────────────────
from statsbombpy import sb          # StatsBomb data
import pandas as pd                 # data filtering and grouping
import matplotlib.pyplot as plt     # drawing figures
from mplsoccer import Pitch         # draws the football pitch
import os                           # creates output folder if it doesn't exist
import warnings
warnings.filterwarnings('ignore')   # suppress the NoAuthWarning we saw earlier
from config import CLUB_COLORS, FALLBACK_COLOR, PITCH_COLOR, FIGURE_COLOR, LINE_COLOR, LINE_ALPHA, ACCENT_COLOR


# ── SETTINGS ─────────────────────────────────────────────────────────────────
# Keeping these at the top makes them easy to change later
MATCH_ID  = 3749448
TEAM      = 'Arsenal'
MIN_PASS_THRESHOLD = 5   # minimum passes between two players to draw a line
                         # (filters out noise from rare/accidental connections)
OUTPUT_PATH = f"outputs/{TEAM.replace(' ', '_').lower()}_passing_network.png"

# Colors loaded from config.py — edit that file to update all scripts at once
TEAM_COLOR = CLUB_COLORS.get(TEAM, FALLBACK_COLOR)
EDGE_COLOR = '#333333'   # lines between players


# ── STEP 1: LOAD MATCH EVENTS ─────────────────────────────────────────────────
print("Loading match events...")
events = sb.events(match_id=MATCH_ID)
print(f"Loaded {len(events)} events\n")


# ── STEP 2: GET ARSENAL'S STARTING XI ────────────────────────────────────────
# StatsBomb stores the lineup inside a special 'Starting XI' event.
# The 'tactics' column of that event contains a 'lineup' list with player names.
print("Extracting starting XI...")

lineup_event = events[
    (events['type'] == 'Starting XI') &
    (events['team'] == TEAM)
]

# The tactics column holds a dict with formation and a lineup list
# Each item in the lineup list has a 'player' key with a 'name' and a 'position'
tactics  = lineup_event.iloc[0]['tactics']
formation = tactics['formation']
starting_xi = [player['player']['name'] for player in tactics['lineup']]

# Identify the goalkeeper — we don't manually exclude them.
# Instead, the threshold filter in Step 7 decides whether they appear.
# If the GK exchanges 5+ passes with any teammate, they'll show up automatically.
# If not, they won't — no manual flag needed.
goalkeeper = next(
    player['player']['name']
    for player in tactics['lineup']
    if player['position']['name'] == 'Goalkeeper'
)

# ── DISPLAY NAME OVERRIDES ────────────────────────────────────────────────────
# Our default logic (last word for 2-word names, first word for 3+) handles most
# players correctly but fails on some names. Add known exceptions here.
# Format: 'Full name as stored in StatsBomb' → 'Display name to show on chart'
DISPLAY_NAME_OVERRIDES = {
    "Sulzeer Jeremiah ''Sol' Campbell": 'Campbell',  # stored with literal quotes in StatsBomb
    'Laureano Bisan-Etame Mayer':       'Lauren',    # hyphenated surname, known by first name
    'Kolo Habib Touré':                 'Touré',     # 3-word name, known by surname
    'Gilberto Aparecido da Silva':      'Gilberto',  # 4-word name, known by first name (same as fallback)
}

print(f"Formation: {formation}")
print(f"Starting XI: {starting_xi}")
print(f"Goalkeeper: {goalkeeper} (will appear only if passing connections clear the threshold)\n")


# ── STEP 3: FIND FIRST SUBSTITUTION MINUTE ────────────────────────────────────
# We only want to show the team's shape before the first change.
# After a sub, the formation often shifts and the picture gets blurry.
substitutions = events[
    (events['type'] == 'Substitution') &
    (events['team'] == TEAM)
]

if len(substitutions) > 0:
    first_sub_minute = substitutions['minute'].min()
    print(f"First Arsenal substitution: minute {first_sub_minute}")
    print(f"Analysing passes from kick-off to minute {first_sub_minute}\n")
else:
    first_sub_minute = 90
    print("No substitutions found — using full match\n")


# ── STEP 4: FILTER TO RELEVANT PASSES ─────────────────────────────────────────
# We want: Arsenal passes | successful | before first sub | between starting XI
#
# How do we know a pass was successful?
# In StatsBomb, pass_outcome is NaN (empty) for successful passes.
# Failed passes have a value like 'Incomplete' or 'Out'.
passes = events[
    (events['type'] == 'Pass') &
    (events['team'] == TEAM) &
    (events['minute'] < first_sub_minute) &
    (events['player'].isin(starting_xi)) &          # full squad — GK included
    (events['pass_recipient'].isin(starting_xi)) &  # threshold decides who appears
    (events['pass_outcome'].isna())                 # NaN = successful
].copy()

print(f"Successful passes between starting XI (before first sub): {len(passes)}\n")


# ── STEP 5: EXTRACT COORDINATES ──────────────────────────────────────────────
# Each 'location' value is stored as a list: [x, y]
# We split these into separate columns so we can do maths on them.
# StatsBomb pitch coordinates: x goes 0→120 (left to right), y goes 0→80 (bottom to top)
passes['x']     = passes['location'].apply(lambda loc: loc[0])
passes['y']     = passes['location'].apply(lambda loc: loc[1])
passes['end_x'] = passes['pass_end_location'].apply(lambda loc: loc[0])
passes['end_y'] = passes['pass_end_location'].apply(lambda loc: loc[1])


# ── STEP 6: CALCULATE AVERAGE POSITIONS ──────────────────────────────────────
# Each player's dot on the network sits at their average passing position.
# This roughly reflects where they spent most of their time on the pitch.
avg_positions = passes.groupby('player').agg(
    avg_x=('x', 'mean'),
    avg_y=('y', 'mean'),
    total_passes=('x', 'count')   # also count total passes made per player
).reset_index()

print("Average positions calculated:")
print(avg_positions[['player', 'avg_x', 'avg_y', 'total_passes']].to_string(index=False))
print()


# ── STEP 7: COUNT PASS COMBINATIONS ──────────────────────────────────────────
# For each pair (Player A → Player B), count how many times that pass happened.
# This becomes the thickness of the connecting line.
pass_combinations = passes.groupby(
    ['player', 'pass_recipient']
).size().reset_index(name='count')

# Filter out weak connections (fewer than MIN_PASS_THRESHOLD).
# This is the only decision point — any player (including the GK) who appears
# in a connection that clears this bar will be drawn. Everyone else won't.
pass_combinations = pass_combinations[
    pass_combinations['count'] >= MIN_PASS_THRESHOLD
]

# Derive the set of players who actually appear in filtered connections.
# This trims avg_positions so we only draw dots for players with at least one
# connection above the threshold — no isolated floating dots.
active_players = set(
    pass_combinations['player'].tolist() +
    pass_combinations['pass_recipient'].tolist()
)
avg_positions = avg_positions[avg_positions['player'].isin(active_players)]

gk_included = goalkeeper in active_players
print(f"Goalkeeper included in network: {gk_included} "
      f"({'cleared threshold' if gk_included else 'below threshold — hidden'})")

# Attach start and end coordinates to each combination
pass_combinations = pass_combinations.merge(
    avg_positions[['player', 'avg_x', 'avg_y']].rename(
        columns={'avg_x': 'x_start', 'avg_y': 'y_start'}
    ),
    on='player'
)
pass_combinations = pass_combinations.merge(
    avg_positions[['player', 'avg_x', 'avg_y']].rename(
        columns={'player': 'pass_recipient', 'avg_x': 'x_end', 'avg_y': 'y_end'}
    ),
    on='pass_recipient'
)

print(f"Pass combinations (with {MIN_PASS_THRESHOLD}+ passes): {len(pass_combinations)}\n")


# ── STEP 8: DRAW THE VISUALIZATION ───────────────────────────────────────────
print("Drawing visualization...")

# Create the pitch
# pitch_type='statsbomb' tells mplsoccer we're using StatsBomb's coordinate system
# pitch_color and line_color set the visual style
pitch = Pitch(
    pitch_type='statsbomb',
    pitch_color=PITCH_COLOR,
    line_color=LINE_COLOR,
    line_alpha=LINE_ALPHA
)

fig, ax = pitch.draw(figsize=(14, 9))
fig.patch.set_facecolor(FIGURE_COLOR)

# DRAW EDGES (lines between players)
# Line thickness and opacity both scale with pass count — more passes = thicker + bolder line
max_count = pass_combinations['count'].max()

for _, row in pass_combinations.iterrows():
    line_width = 1 + (row['count'] / max_count) * 9
    alpha      = 0.2 + (row['count'] / max_count) * 0.6

    pitch.lines(
        row['x_start'], row['y_start'],
        row['x_end'],   row['y_end'],
        lw=line_width,
        color=EDGE_COLOR,
        alpha=alpha,
        ax=ax,
        zorder=1
    )

# DRAW NODES (player dots)
# Node size scales with total passes — more active players have bigger dots
max_passes = avg_positions['total_passes'].max()

for _, row in avg_positions.iterrows():
    node_size = 300 + (row['total_passes'] / max_passes) * 700

    pitch.scatter(
        row['avg_x'], row['avg_y'],
        s=node_size,
        color=TEAM_COLOR,       # automatically uses the club's official color
        edgecolors='white',
        linewidth=2,
        ax=ax,
        zorder=2
    )

    # Label: get the player's display name
    # First check the override dictionary for known problem names.
    # Fall back to: last word for 2-word names, first word for 3+ word names.
    parts = row['player'].split()
    display_name = DISPLAY_NAME_OVERRIDES.get(
        row['player'],
        parts[-1] if len(parts) <= 2 else parts[0]
    )

    ax.annotate(
        display_name,
        xy=(row['avg_x'], row['avg_y']),
        fontsize=10,            # larger than before
        color=ACCENT_COLOR,
        fontweight='bold',
        ha='center',
        va='bottom',
        xytext=(0, 12),
        textcoords='offset points',
        zorder=3,
        bbox=dict(             # subtle dark box behind name for readability
            boxstyle='round,pad=0.2',
            facecolor=PITCH_COLOR,
            alpha=0.6,
            edgecolor='none'
        )
    )

# ATTACK DIRECTION ARROW
# Arsenal attacks left to right in StatsBomb coordinates (x: 0 → 120)
# We draw a small arrow at the bottom of the pitch to make this clear
ax.annotate(
    '',
    xy=(110, 76), xytext=(90, 76),
    arrowprops=dict(arrowstyle='->', color=ACCENT_COLOR, lw=1.5)
)
ax.text(100, 78, 'Attacking direction', color=ACCENT_COLOR,
        fontsize=7.5, ha='center', va='bottom', style='italic')


# LEGEND
# Placed at figure level (not inside the pitch axes) so it never overlaps pitch lines.
# fig.text() uses normalised coordinates: (0,0) = bottom-left, (1,1) = top-right of figure.
legend_text = '● Node size = passes made          ─  Line width = pass frequency'
fig.text(
    0.5, 0.01,
    legend_text,
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
    f'Arsenal Passing Network\nArsenal 4–2 Liverpool  |  Premier League 2003/04\n'
    f'Formation: {formation}  |  Starting XI only, before first substitution',
    color=ACCENT_COLOR,
    fontsize=12,
    fontweight='bold',
    pad=20
)


# ── STEP 9: SAVE THE IMAGE ────────────────────────────────────────────────────
os.makedirs('outputs', exist_ok=True)   # create outputs folder if it doesn't exist
plt.tight_layout()
plt.savefig(OUTPUT_PATH, dpi=150, bbox_inches='tight', facecolor=FIGURE_COLOR)
plt.close()

print(f"\nDone! Image saved to: {OUTPUT_PATH}")
print("Open that file to see your passing network.")
