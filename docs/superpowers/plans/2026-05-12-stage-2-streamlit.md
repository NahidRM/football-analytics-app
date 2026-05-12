# Stage 2 — Streamlit Prototype Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Wrap the four Stage 1 visualization scripts in a Streamlit web UI so Nahid can pick a match, choose an analysis type, and see the chart in a browser — no terminal required.

**Architecture:** Refactor each visualization script to expose a `draw_*()` function that accepts a pre-loaded events DataFrame and returns a `matplotlib.Figure`. A new `data_loader.py` handles all StatsBomb API calls with Streamlit caching. `app.py` wires everything together: sidebar for match selection, main area for the chart.

**Tech Stack:** Streamlit, statsbombpy, mplsoccer, matplotlib, pandas, pytest

---

## File Map

| Status | File | Responsibility |
|--------|------|----------------|
| NEW | `src/data_loader.py` | StatsBomb API calls + `@st.cache_data` caching |
| NEW | `src/app.py` | Streamlit UI: sidebar selectors + chart display |
| NEW | `tests/test_data_loader.py` | Data layer tests |
| NEW | `tests/test_visualizations.py` | Smoke tests for draw_* functions |
| MODIFY | `src/passing_network.py` | Add `draw_passing_network()` function; keep `__main__` block |
| MODIFY | `src/heat_map.py` | Add `draw_heat_map()` function; keep `__main__` block |
| MODIFY | `src/shot_map.py` | Add `draw_shot_map()` function; keep `__main__` block |
| MODIFY | `src/press_map.py` | Add `draw_press_map()` function; keep `__main__` block |
| MODIFY | `requirements.txt` | Add `streamlit`, `pytest` |
| UNCHANGED | `src/config.py` | No changes needed |
| UNCHANGED | `src/explore_data.py` | No changes needed |

---

## Task 1: Add dependencies

**Files:**
- Modify: `requirements.txt`

- [ ] **Step 1: Add streamlit and pytest to requirements.txt**

Replace the full file with:
```
statsbombpy
mplsoccer
pandas
numpy
matplotlib
Pillow
streamlit
pytest
```

- [ ] **Step 2: Install new dependencies**

```bash
cd "/Users/nahidmuzammil/Documents/Claude/Projects/Analysis app"
source venv/bin/activate
pip install streamlit pytest
```

Expected: both packages install without error.

- [ ] **Step 3: Verify streamlit is installed**

```bash
streamlit --version
```

Expected: prints a version number like `Streamlit, version 1.x.x`

- [ ] **Step 4: Commit**

```bash
git add requirements.txt
git commit -m "chore: add streamlit and pytest to requirements"
```

---

## Task 2: Create data_loader.py

**Files:**
- Create: `src/data_loader.py`

- [ ] **Step 1: Write the failing test first (in Task 3 — but read this to understand what data_loader must produce)**

The functions to build:
- `get_competitions()` → DataFrame with columns `competition_id`, `season_id`, `competition_name`, `season_name`, `country_name`
- `get_matches(competition_id, season_id)` → DataFrame with columns `match_id`, `home_team`, `away_team`, `home_score`, `away_score`, `match_date`
- `get_events(match_id)` → DataFrame with columns `type`, `team`, `player`, `location`, `minute`

- [ ] **Step 2: Create src/data_loader.py**

```python
# data_loader.py
#
# PURPOSE: All StatsBomb API calls live here.
# @st.cache_data tells Streamlit: "once you've fetched this, remember it".
# This means the app doesn't re-fetch the same match data every time the
# user clicks a button — it serves the cached result instead. Faster app,
# fewer unnecessary network calls.

import streamlit as st
from statsbombpy import sb
import warnings
warnings.filterwarnings('ignore')


@st.cache_data
def get_competitions():
    """Return all available StatsBomb competitions as a DataFrame."""
    return sb.competitions()


@st.cache_data
def get_matches(competition_id: int, season_id: int):
    """Return all matches for a given competition and season."""
    return sb.matches(competition_id=competition_id, season_id=season_id)


@st.cache_data
def get_events(match_id: int):
    """Return all events for a given match."""
    return sb.events(match_id=match_id)
```

- [ ] **Step 3: Commit**

```bash
git add src/data_loader.py
git commit -m "feat: add data_loader with cached StatsBomb API calls"
```

---

## Task 3: Write data_loader tests

**Files:**
- Create: `tests/test_data_loader.py`

Note: these tests hit the real StatsBomb API (no mocking). They are slow (~5–10s each) but they verify the actual data contract. Run them once after writing, not on every save.

- [ ] **Step 1: Create tests directory**

```bash
mkdir -p "/Users/nahidmuzammil/Documents/Claude/Projects/Analysis app/tests"
```

- [ ] **Step 2: Create tests/test_data_loader.py**

```python
# test_data_loader.py
#
# These are integration tests — they hit the real StatsBomb API.
# Run with: pytest tests/test_data_loader.py -v
# Expected runtime: ~15-30 seconds total (network calls)

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import pandas as pd

# We import the raw statsbombpy functions directly (not through data_loader)
# because data_loader uses @st.cache_data which requires a running Streamlit app.
from statsbombpy import sb
import warnings
warnings.filterwarnings('ignore')


def test_competitions_returns_dataframe():
    comps = sb.competitions()
    assert isinstance(comps, pd.DataFrame)


def test_competitions_has_required_columns():
    comps = sb.competitions()
    required = {'competition_id', 'season_id', 'competition_name', 'season_name'}
    assert required.issubset(set(comps.columns))


def test_matches_returns_dataframe_for_known_competition():
    # Premier League 2003/04: competition_id=2, season_id=44
    matches = sb.matches(competition_id=2, season_id=44)
    assert isinstance(matches, pd.DataFrame)
    assert len(matches) > 0


def test_matches_has_required_columns():
    matches = sb.matches(competition_id=2, season_id=44)
    required = {'match_id', 'home_team', 'away_team', 'home_score', 'away_score'}
    assert required.issubset(set(matches.columns))


def test_events_returns_dataframe_for_known_match():
    events = sb.events(match_id=3749448)
    assert isinstance(events, pd.DataFrame)
    assert len(events) > 0


def test_events_has_required_columns():
    events = sb.events(match_id=3749448)
    required = {'type', 'team', 'player', 'location', 'minute'}
    assert required.issubset(set(events.columns))


def test_events_contains_expected_event_types():
    events = sb.events(match_id=3749448)
    event_types = set(events['type'].unique())
    for expected in ['Pass', 'Shot', 'Pressure']:
        assert expected in event_types, f"Expected event type '{expected}' not found"
```

- [ ] **Step 3: Run tests to verify they pass**

```bash
cd "/Users/nahidmuzammil/Documents/Claude/Projects/Analysis app"
source venv/bin/activate
pytest tests/test_data_loader.py -v
```

Expected output: 7 tests, all PASSED. (Will take ~20s due to network calls.)

- [ ] **Step 4: Commit**

```bash
git add tests/test_data_loader.py
git commit -m "test: add data_loader integration tests"
```

---

## Task 4: Refactor passing_network.py

**Files:**
- Modify: `src/passing_network.py`

The refactor pattern: wrap all the processing + drawing logic in a function. Keep the top-level settings block at the bottom under `if __name__ == '__main__':` so the script still works standalone.

- [ ] **Step 1: Rewrite src/passing_network.py**

Replace the entire file content with:

```python
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
from config import (
    CLUB_COLORS, FALLBACK_COLOR, PITCH_COLOR, FIGURE_COLOR,
    LINE_COLOR, LINE_ALPHA, ACCENT_COLOR
)

MIN_PASS_THRESHOLD = 5
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
    display_name_overrides: dict = None
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
    goalkeeper = next(
        p['player']['name'] for p in tactics['lineup']
        if p['position']['name'] == 'Goalkeeper'
    )

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
    pass_combinations = pass_combinations[pass_combinations['count'] >= MIN_PASS_THRESHOLD]

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
```

- [ ] **Step 2: Verify the standalone script still works**

```bash
cd "/Users/nahidmuzammil/Documents/Claude/Projects/Analysis app"
source venv/bin/activate
python3 src/passing_network.py
```

Expected: prints "Done! Image saved to outputs/arsenal_passing_network.png" and the file is updated.

- [ ] **Step 3: Commit**

```bash
git add src/passing_network.py
git commit -m "refactor: expose draw_passing_network() function"
```

---

## Task 5: Refactor heat_map.py

**Files:**
- Modify: `src/heat_map.py`

- [ ] **Step 1: Rewrite src/heat_map.py**

```python
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
from config import (
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
```

- [ ] **Step 2: Verify standalone still works**

```bash
python3 src/heat_map.py
```

Expected: prints "Done! Image saved to outputs/thierry_henry_heat_map.png"

- [ ] **Step 3: Commit**

```bash
git add src/heat_map.py
git commit -m "refactor: expose draw_heat_map() function"
```

---

## Task 6: Refactor shot_map.py

**Files:**
- Modify: `src/shot_map.py`

- [ ] **Step 1: Rewrite src/shot_map.py**

```python
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
from config import (
    CLUB_COLORS, FALLBACK_COLOR, PITCH_COLOR, FIGURE_COLOR,
    LINE_COLOR, LINE_ALPHA, ACCENT_COLOR, GOAL_COLOR
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
```

- [ ] **Step 2: Verify standalone still works**

```bash
python3 src/shot_map.py
```

Expected: prints "Done! Image saved to outputs/arsenal_shot_map.png"

- [ ] **Step 3: Commit**

```bash
git add src/shot_map.py
git commit -m "refactor: expose draw_shot_map() function"
```

---

## Task 7: Refactor press_map.py

**Files:**
- Modify: `src/press_map.py`

- [ ] **Step 1: Rewrite src/press_map.py**

```python
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
from config import (
    CLUB_COLORS, FALLBACK_COLOR, PITCH_COLOR, FIGURE_COLOR,
    LINE_COLOR, LINE_ALPHA, ACCENT_COLOR, PRESS_COLOR
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
```

- [ ] **Step 2: Verify standalone still works**

```bash
python3 src/press_map.py
```

Expected: prints "Done! Image saved to outputs/arsenal_press_map.png"

- [ ] **Step 3: Commit**

```bash
git add src/press_map.py
git commit -m "refactor: expose draw_press_map() function"
```

---

## Task 8: Write visualization smoke tests

**Files:**
- Create: `tests/test_visualizations.py`

These tests load a real match and verify each draw_* function returns a Figure without crashing. They run once to confirm the refactor didn't break anything.

- [ ] **Step 1: Create tests/test_visualizations.py**

```python
# test_visualizations.py
#
# Smoke tests for visualization functions.
# Verifies: each draw_* function runs without crashing and returns a Figure.
# Run with: pytest tests/test_visualizations.py -v
# Expected runtime: ~10-15 seconds (one network call to load events, then local drawing)

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import pytest
import matplotlib
matplotlib.use('Agg')   # non-interactive backend — no pop-up windows during tests
import matplotlib.pyplot as plt
from statsbombpy import sb
import warnings
warnings.filterwarnings('ignore')

from passing_network import draw_passing_network
from heat_map import draw_heat_map
from shot_map import draw_shot_map
from press_map import draw_press_map

MATCH_LABEL = 'Arsenal 4–2 Liverpool | Premier League 2003/04'


@pytest.fixture(scope='module')
def events():
    """Load match events once and share across all tests in this module."""
    return sb.events(match_id=3749448)


def test_draw_passing_network_returns_figure(events):
    fig = draw_passing_network(events, 'Arsenal', MATCH_LABEL)
    assert isinstance(fig, plt.Figure)
    plt.close(fig)


def test_draw_heat_map_returns_figure(events):
    fig = draw_heat_map(events, 'Thierry Henry', 'Arsenal', MATCH_LABEL)
    assert isinstance(fig, plt.Figure)
    plt.close(fig)


def test_draw_heat_map_raises_for_unknown_player(events):
    with pytest.raises(ValueError, match="No touch events found"):
        draw_heat_map(events, 'Fake Player', 'Arsenal', MATCH_LABEL)


def test_draw_shot_map_returns_figure(events):
    fig = draw_shot_map(events, 'Arsenal', MATCH_LABEL)
    assert isinstance(fig, plt.Figure)
    plt.close(fig)


def test_draw_press_map_returns_figure(events):
    fig = draw_press_map(events, 'Arsenal', MATCH_LABEL)
    assert isinstance(fig, plt.Figure)
    plt.close(fig)
```

- [ ] **Step 2: Run tests to verify they all pass**

```bash
pytest tests/test_visualizations.py -v
```

Expected: 5 tests, all PASSED.

- [ ] **Step 3: Commit**

```bash
git add tests/test_visualizations.py
git commit -m "test: add visualization smoke tests"
```

---

## Task 9: Build app.py — match selection

**Files:**
- Create: `src/app.py`

This task builds the sidebar match-selection UI only. The visualization display is Task 10.

- [ ] **Step 1: Create src/app.py**

```python
# app.py
#
# PURPOSE: Streamlit UI for the Football Analytics App.
# Run with: streamlit run src/app.py (from the project root with venv active)
#
# HOW STREAMLIT WORKS:
# Streamlit re-runs the entire script from top to bottom every time the user
# interacts with any widget (dropdown, button, etc.). State is managed through
# st.session_state. @st.cache_data prevents re-fetching data on every re-run.

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
from passing_network import draw_passing_network
from heat_map import draw_heat_map
from shot_map import draw_shot_map
from press_map import draw_press_map

# ── PAGE CONFIG ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title='Football Analytics',
    page_icon='⚽',
    layout='wide'
)

st.title('⚽ Football Analytics')

# ── SIDEBAR — MATCH SELECTION ──────────────────────────────────────────────────
with st.sidebar:
    st.header('Match Selection')

    # Step 1: Load all available competitions
    competitions = data_loader.get_competitions()

    # Build a human-readable label for each competition+season row
    # e.g. "Premier League 2003/04 (England)"
    competitions['label'] = (
        competitions['competition_name'] + ' ' +
        competitions['season_name'] + ' (' +
        competitions['country_name'] + ')'
    )
    competitions = competitions.sort_values('label')

    selected_label = st.selectbox('Competition & Season', competitions['label'].tolist())
    selected_row   = competitions[competitions['label'] == selected_label].iloc[0]

    competition_id = int(selected_row['competition_id'])
    season_id      = int(selected_row['season_id'])

    # Step 2: Load matches for the selected competition+season
    matches = data_loader.get_matches(competition_id, season_id)

    # Build a human-readable label: "Arsenal 4-2 Liverpool (2003-11-15)"
    matches['label'] = (
        matches['home_team'] + ' ' +
        matches['home_score'].astype(str) + '–' +
        matches['away_score'].astype(str) + ' ' +
        matches['away_team'] + ' (' +
        matches['match_date'].astype(str) + ')'
    )
    matches = matches.sort_values('match_date', ascending=False)

    selected_match_label = st.selectbox('Match', matches['label'].tolist())
    selected_match = matches[matches['label'] == selected_match_label].iloc[0]
    match_id = int(selected_match['match_id'])

    # Step 3: Team selection (home or away)
    home_team = selected_match['home_team']
    away_team = selected_match['away_team']
    selected_team = st.radio('Team to analyse', [home_team, away_team])

    # Step 4: Analysis type
    st.divider()
    st.header('Analysis')
    analysis_options = ['Passing Network', 'Heat Map', 'Shot Map', 'Press Map']
    selected_analysis = st.selectbox('Analysis Type', analysis_options)

    # Step 5: Player selector — only shown for Heat Map
    selected_player = None
    if selected_analysis == 'Heat Map':
        events_preview = data_loader.get_events(match_id)
        team_players = sorted(
            events_preview[
                (events_preview['team'] == selected_team) &
                (events_preview['player'].notna())
            ]['player'].unique().tolist()
        )
        selected_player = st.selectbox('Player', team_players)

    # Step 6: Run button
    st.divider()
    run = st.button('Generate Visualization', type='primary', use_container_width=True)

# ── MAIN AREA — VISUALIZATION ──────────────────────────────────────────────────
# Build a match label for chart titles
score_label = (
    f"{selected_match['home_team']} "
    f"{selected_match['home_score']}–{selected_match['away_score']} "
    f"{selected_match['away_team']}"
)
match_label = f"{score_label} | {selected_row['competition_name']} {selected_row['season_name']}"

if run:
    with st.spinner('Loading match data...'):
        events = data_loader.get_events(match_id)

    with st.spinner(f'Drawing {selected_analysis}...'):
        try:
            if selected_analysis == 'Passing Network':
                fig = draw_passing_network(events, selected_team, match_label)
            elif selected_analysis == 'Heat Map':
                fig = draw_heat_map(events, selected_player, selected_team, match_label)
            elif selected_analysis == 'Shot Map':
                fig = draw_shot_map(events, selected_team, match_label)
            elif selected_analysis == 'Press Map':
                fig = draw_press_map(events, selected_team, match_label)

            st.pyplot(fig)

            # Save the figure to a bytes buffer for the download button
            buf = io.BytesIO()
            fig.savefig(buf, format='png', dpi=150, bbox_inches='tight')
            buf.seek(0)

            filename = (
                f"{selected_team.replace(' ', '_').lower()}_"
                f"{selected_analysis.replace(' ', '_').lower()}.png"
            )
            st.download_button(
                label='Download Image',
                data=buf,
                file_name=filename,
                mime='image/png'
            )

            plt.close(fig)

        except ValueError as e:
            st.error(str(e))
        except Exception as e:
            st.error(f'Something went wrong: {e}')

else:
    st.info('Configure your selection in the sidebar and click **Generate Visualization**.')
```

- [ ] **Step 2: Commit**

```bash
git add src/app.py
git commit -m "feat: add Streamlit app with match selection and visualization display"
```

---

## Task 10: Run and test the app

- [ ] **Step 1: Start the Streamlit app**

```bash
cd "/Users/nahidmuzammil/Documents/Claude/Projects/Analysis app"
source venv/bin/activate
streamlit run src/app.py
```

Expected: browser opens at `http://localhost:8501` showing the Football Analytics app.

- [ ] **Step 2: Test the golden path**

1. In sidebar: select "Premier League 2003/04 (England)" → the Arsenal match should appear
2. Select the Arsenal 4–2 Liverpool match
3. Select "Arsenal" as team
4. Select "Passing Network"
5. Click "Generate Visualization"
6. Verify the passing network appears in the main area
7. Click "Download Image" — verify a PNG downloads

- [ ] **Step 3: Test the heat map player picker**

1. Change Analysis Type to "Heat Map"
2. Verify a player dropdown appears in the sidebar
3. Select "Thierry Henry"
4. Click "Generate Visualization"
5. Verify the heat map appears

- [ ] **Step 4: Test all four analysis types**

Repeat for Shot Map and Press Map. Verify each renders without errors.

- [ ] **Step 5: Test switching teams**

Select "Liverpool" instead of Arsenal. Run Passing Network. Verify it shows Liverpool in red (their club color), not Arsenal.

- [ ] **Step 6: Commit**

```bash
git add -A
git commit -m "feat: Stage 2 complete — Streamlit prototype working"
```

---

## Stage 2 Complete ✓

**What you now have:**
- A browser-based UI at `http://localhost:8501`
- Pick any StatsBomb match from a dropdown
- Choose analysis type and team
- See the visualization instantly, download as PNG
- All four Stage 1 scripts still work standalone

**Next:** Stage 3 — integrate the Claude API for AI content generation.
See `docs/superpowers/plans/2026-05-12-stage-3-claude-api.md`
