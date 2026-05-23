# Warm-Up Games & Dev Server Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Surface international warm-up/friendly matches in the app before FIFA World Cup 2026 starts, and add a single-command dev server.

**Architecture:** Add `is_warmup` to the `Match` dataclass so the frontend can distinguish warm-up games from live matches and show an orange WARM-UP badge. Extend `WorldCupProvider` to fetch both league ID 1 (World Cup) and league ID 10 (Friendlies), filtering out youth matches. Clean up stale `APP_MODE` config while touching `config.py`. Add `concurrently` to run both servers from one terminal.

**Tech Stack:** Python dataclasses, API-Football REST API, TypeScript/React, Next.js, concurrently (npm)

---

## File Map

| Action | File | What changes |
|--------|------|--------------|
| Modify | `backend/providers/base.py` | Add `is_warmup: bool = False` to `Match` |
| Modify | `frontend/lib/api.ts` | Add `is_warmup: boolean` to `Match` interface |
| Modify | `backend/config.py` | Remove `APP_MODE` and its validation |
| Modify | `backend/tests/test_config.py` | Remove three `APP_MODE` tests |
| Modify | `backend/providers/world_cup.py` | Add `_LEAGUES`, `_YOUTH` regex, update `_parse_fixtures` + `get_matches` |
| Modify | `backend/tests/test_world_cup_provider.py` | Pass league dict to `_parse_fixtures`, add warmup + youth filter tests |
| Modify | `frontend/components/MatchSelector.tsx` | Carry `is_warmup` in competitions map, render WARM-UP badge |
| Modify | `frontend/package.json` | Add `concurrently` dev dependency + `dev:all` script |

---

## Task 1: Add `is_warmup` to the Match data model

**Files:**
- Modify: `backend/providers/base.py`
- Modify: `frontend/lib/api.ts`

- [ ] **Step 1: Write a failing test for `is_warmup` default**

Add to `backend/tests/test_config.py` (below the existing `test_world_cup_analyses` test):

```python
def test_match_is_warmup_defaults_false():
    from backend.providers.base import Match
    m = Match(
        match_id="sb:1", label="Test", home_team="A", away_team="B",
        home_score=0, away_score=0, date="2026-06-01",
    )
    assert m.is_warmup == False


def test_match_is_warmup_can_be_set():
    from backend.providers.base import Match
    m = Match(
        match_id="apf:1", label="Test", home_team="A", away_team="B",
        home_score=0, away_score=0, date="2026-06-01",
        is_warmup=True,
    )
    assert m.is_warmup == True
```

- [ ] **Step 2: Run the tests to verify they fail**

```bash
cd "/Users/nahidmuzammil/Documents/Claude/Projects/Analysis app"
python -m pytest backend/tests/test_config.py::test_match_is_warmup_defaults_false backend/tests/test_config.py::test_match_is_warmup_can_be_set -v
```

Expected: `AttributeError: Match has no field 'is_warmup'`

- [ ] **Step 3: Add `is_warmup` to the `Match` dataclass**

In `backend/providers/base.py`, add the field after `is_live`:

```python
@dataclass
class Match:
    match_id: str
    label: str
    home_team: str
    away_team: str
    home_score: int
    away_score: int
    date: str
    competition: str = ""
    season: str = ""
    country: str = ""
    is_live: bool = False
    is_warmup: bool = False
```

- [ ] **Step 4: Add `is_warmup` to the TypeScript `Match` interface**

In `frontend/lib/api.ts`, add after `is_live`:

```typescript
export interface Match {
  match_id: string;
  label: string;
  home_team: string;
  away_team: string;
  home_score: number;
  away_score: number;
  date: string;
  competition: string;
  season: string;
  country: string;
  is_live: boolean;
  is_warmup: boolean;
}
```

- [ ] **Step 5: Run the tests to verify they pass**

```bash
python -m pytest backend/tests/test_config.py::test_match_is_warmup_defaults_false backend/tests/test_config.py::test_match_is_warmup_can_be_set -v
```

Expected: both `PASSED`

- [ ] **Step 6: Add `is_warmup` to both API responses in `backend/main.py`**

`main.py` manually serialises `Match` fields. Two places need updating:

In `list_matches()`, add `"is_warmup": m.is_warmup,` after `"is_live"`:

```python
@app.get("/matches")
def list_matches():
    return [
        {
            "match_id": m.match_id,
            "label": m.label,
            "home_team": m.home_team,
            "away_team": m.away_team,
            "home_score": m.home_score,
            "away_score": m.away_score,
            "date": m.date,
            "competition": m.competition,
            "season": m.season,
            "country": m.country,
            "is_live": m.is_live,
            "is_warmup": m.is_warmup,
        }
        for m in get_all_matches()
    ]
```

In `get_match()`, add `"is_warmup": match.is_warmup if match else False,` after `"is_live"`:

```python
    return {
        "match_id": match_id,
        "label": match.label if match else match_id,
        "home_team": match.home_team if match else home_team,
        "away_team": match.away_team if match else away_team,
        "home_score": match.home_score if match else 0,
        "away_score": match.away_score if match else 0,
        "date": match.date if match else "",
        "competition": match.competition if match else "",
        "season": match.season if match else "",
        "country": match.country if match else "",
        "is_live": match.is_live if match else False,
        "is_warmup": match.is_warmup if match else False,
        "fbref_available": shot_data is not None,
        "available_analyses": get_available_analyses(match_id),
        "home_players": home_players,
        "away_players": away_players,
    }
```

- [ ] **Step 7: Run the full test suite to check nothing is broken**

```bash
python -m pytest backend/tests/ -v
```

Expected: all existing tests pass (APP_MODE tests will still pass here — they're removed in Task 2).

- [ ] **Step 8: Commit**

```bash
git add backend/providers/base.py backend/main.py frontend/lib/api.ts backend/tests/test_config.py
git commit -m "feat: add is_warmup field to Match dataclass, API responses, and TypeScript interface"
```

---

## Task 2: Remove stale APP_MODE from config

**Files:**
- Modify: `backend/config.py`
- Modify: `backend/tests/test_config.py`

`APP_MODE` was used to switch between providers before namespaced match IDs were introduced. Routing is now done by prefix (`sb:` / `apf:`). The variable is read nowhere outside `config.py` and its own tests.

- [ ] **Step 1: Remove APP_MODE from `backend/config.py`**

Replace the current `config.py` content with (keeping everything except the APP_MODE block):

```python
import os
from dotenv import load_dotenv

load_dotenv(override=True)

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
API_FOOTBALL_KEY = os.getenv("API_FOOTBALL_KEY", "")
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "")

# ── CLUB COLORS ───────────────────────────────────────────────────────────────
# Official primary colors for each club. Add new clubs here — all scripts
# will pick them up automatically via CLUB_COLORS.get(TEAM, FALLBACK_COLOR).
CLUB_COLORS = {
    'Arsenal':              '#EF0107',
    'Liverpool':            '#C8102E',
    'Chelsea':              '#034694',
    'Manchester City':      '#6CABDD',
    'Manchester United':    '#DA291C',
    'Tottenham Hotspur':    '#132257',
    'Newcastle United':     '#241F20',
    'Aston Villa':          '#95BFE5',
    'West Ham United':      '#7A263A',
    'Barcelona':            '#A50044',
    'Real Madrid':          '#FEBE10',
    'Bayern München':       '#DC052D',
    'Borussia Dortmund':    '#FDE100',
    'Paris Saint-Germain':  '#003F8A',
}

FALLBACK_COLOR = '#333333'   # used when a club isn't in CLUB_COLORS yet

# ── PITCH STYLE ───────────────────────────────────────────────────────────────
# Shared visual theme across all scripts. Change here to update all outputs.
PITCH_COLOR  = '#F0F2F5'   # cool light grey
FIGURE_COLOR = '#F0F2F5'
LINE_COLOR   = '#aaaaaa'   # subtle grey pitch markings
LINE_ALPHA   = 0.6
ACCENT_COLOR = '#222222'   # text, arrows, borders

# ── PRESS MAP ─────────────────────────────────────────────────────────────────
# Press maps always use purple — visually distinct from player heat maps.
# Purple signals defensive stubbornness regardless of which team is analysed.
PRESS_COLOR = '#7B2FBE'

# ── SHOT MAP ──────────────────────────────────────────────────────────────────
GOAL_COLOR = '#00C853'     # bright green — universally reads as "success"
```

- [ ] **Step 2: Remove the three APP_MODE tests from `backend/tests/test_config.py`**

Delete `test_app_mode_statsbomb`, `test_app_mode_world_cup`, and `test_invalid_app_mode_raises`. Keep `test_statsbomb_analyses`, `test_world_cup_analyses`, and the two `is_warmup` tests added in Task 1. The file should look like:

```python
import pytest
from backend.visualizations import get_available_analyses


def test_statsbomb_analyses():
    result = get_available_analyses("sb:1")
    assert "passing_network" in result
    assert "match_stats" not in result


def test_world_cup_analyses():
    result = get_available_analyses("apf:1")
    assert "match_stats" in result
    assert "player_ratings" in result
    assert "xg_timeline" in result
    assert "passing_network" not in result


def test_match_is_warmup_defaults_false():
    from backend.providers.base import Match
    m = Match(
        match_id="sb:1", label="Test", home_team="A", away_team="B",
        home_score=0, away_score=0, date="2026-06-01",
    )
    assert m.is_warmup == False


def test_match_is_warmup_can_be_set():
    from backend.providers.base import Match
    m = Match(
        match_id="apf:1", label="Test", home_team="A", away_team="B",
        home_score=0, away_score=0, date="2026-06-01",
        is_warmup=True,
    )
    assert m.is_warmup == True
```

- [ ] **Step 3: Run the full test suite**

```bash
python -m pytest backend/tests/ -v
```

Expected: all tests pass, three APP_MODE tests are gone, everything else green.

- [ ] **Step 4: Commit**

```bash
git add backend/config.py backend/tests/test_config.py
git commit -m "chore: remove stale APP_MODE config — routing now handled by match ID prefix"
```

---

## Task 3: Extend WorldCupProvider for friendlies + youth filter

**Files:**
- Modify: `backend/providers/world_cup.py`
- Modify: `backend/tests/test_world_cup_provider.py`

- [ ] **Step 1: Write failing tests**

Replace the content of `backend/tests/test_world_cup_provider.py` with:

```python
import pytest
from unittest.mock import patch, MagicMock
from backend.providers.world_cup import WorldCupProvider, _YOUTH
from backend.providers.base import Match, MatchStats, Lineup


FAKE_WC_LEAGUE = {"id": 1, "season": 2026, "name": "FIFA World Cup 2026", "is_warmup": False}
FAKE_FRIENDLY_LEAGUE = {"id": 10, "season": 2026, "name": "International Friendlies", "is_warmup": True}

FAKE_FIXTURES_RESPONSE = {
    "response": [
        {
            "fixture": {
                "id": 12345,
                "date": "2026-06-15T15:00:00+00:00",
                "status": {"short": "FT"},
            },
            "teams": {
                "home": {"name": "France"},
                "away": {"name": "Morocco"},
            },
            "goals": {"home": 2, "away": 1},
            "league": {"name": "FIFA World Cup", "season": 2026},
        }
    ]
}

FAKE_STATS_RESPONSE = {
    "response": [
        {
            "team": {"name": "France"},
            "statistics": [
                {"type": "Ball Possession", "value": "60%"},
                {"type": "Total Shots", "value": "14"},
                {"type": "Shots on Goal", "value": "6"},
                {"type": "Total passes", "value": "520"},
                {"type": "Passes %", "value": "89%"},
                {"type": "Corner Kicks", "value": "5"},
                {"type": "Fouls", "value": "12"},
            ],
        },
        {
            "team": {"name": "Morocco"},
            "statistics": [
                {"type": "Ball Possession", "value": "40%"},
                {"type": "Total Shots", "value": "8"},
                {"type": "Shots on Goal", "value": "3"},
                {"type": "Total passes", "value": "340"},
                {"type": "Passes %", "value": "82%"},
                {"type": "Corner Kicks", "value": "3"},
                {"type": "Fouls", "value": "15"},
            ],
        },
    ]
}


def test_parse_matches():
    provider = WorldCupProvider.__new__(WorldCupProvider)
    matches = provider._parse_fixtures(FAKE_FIXTURES_RESPONSE["response"], FAKE_WC_LEAGUE)
    assert len(matches) == 1
    m = matches[0]
    assert m.match_id == "apf:12345"
    assert m.home_team == "France"
    assert m.away_team == "Morocco"
    assert m.home_score == 2
    assert m.away_score == 1
    assert m.is_warmup == False
    assert m.competition == "FIFA World Cup 2026"


def test_parse_warmup_matches():
    provider = WorldCupProvider.__new__(WorldCupProvider)
    matches = provider._parse_fixtures(FAKE_FIXTURES_RESPONSE["response"], FAKE_FRIENDLY_LEAGUE)
    assert len(matches) == 1
    m = matches[0]
    assert m.is_warmup == True
    assert m.competition == "International Friendlies"
    assert m.is_live == True


def test_youth_filter_regex():
    # These should be blocked
    assert _YOUTH.search("Hungary U17")
    assert _YOUTH.search("Tajikistan U20")
    assert _YOUTH.search("England U21")
    assert _YOUTH.search("Brazil U23")
    # These should NOT be blocked
    assert not _YOUTH.search("Uruguay")
    assert not _YOUTH.search("France")
    assert not _YOUTH.search("Mexico")


def test_parse_match_stats():
    provider = WorldCupProvider.__new__(WorldCupProvider)
    stats = provider._parse_match_stats("France", "Morocco", FAKE_STATS_RESPONSE["response"])
    assert stats.home_team == "France"
    assert stats.home.possession == 60.0
    assert stats.home.shots == 14
    assert stats.away.shots == 8


def test_get_stat_value():
    provider = WorldCupProvider.__new__(WorldCupProvider)
    stat_list = [{"type": "Total Shots", "value": "14"}, {"type": "Fouls", "value": "12"}]
    assert provider._get_stat(stat_list, "Total Shots", int) == 14
    assert provider._get_stat(stat_list, "Missing", int, default=0) == 0


def test_get_shot_data_returns_none_on_fbref_failure():
    provider = WorldCupProvider.__new__(WorldCupProvider)
    import sys
    original = sys.modules.pop("soccerdata", None)
    sys.modules["soccerdata"] = None  # type: ignore
    try:
        result = provider.get_shot_data("apf:12345")
        assert result is None
    finally:
        if original is not None:
            sys.modules["soccerdata"] = original
        else:
            sys.modules.pop("soccerdata", None)


def test_parse_fbref_shots_returns_none_on_none_input():
    provider = WorldCupProvider.__new__(WorldCupProvider)
    result = provider._parse_fbref_shots(None, None)
    assert result is None
```

- [ ] **Step 2: Run to verify the new tests fail**

```bash
python -m pytest backend/tests/test_world_cup_provider.py::test_parse_warmup_matches backend/tests/test_world_cup_provider.py::test_youth_filter_regex -v
```

Expected: `ImportError` or `TypeError` — `_YOUTH` not defined, `_parse_fixtures` doesn't accept a league arg.

- [ ] **Step 3: Update `backend/providers/world_cup.py`**

Replace the top of the file (up to and including the class definition preamble) with:

```python
from __future__ import annotations
import logging
import re
import requests
import warnings
warnings.filterwarnings("ignore")

from backend.config import API_FOOTBALL_KEY
from .base import (
    DataProvider, Match, MatchStats, TeamStats,
    PlayerStat, Shot, Lineup
)

_BASE_URL = "https://v3.football.api-sports.io"

_LEAGUES = [
    {"id": 1,  "season": 2026, "name": "FIFA World Cup 2026",     "is_warmup": False},
    {"id": 10, "season": 2026, "name": "International Friendlies", "is_warmup": True},
]

# Matches any team name containing an age group (U17, U20, U21, U23, etc.)
# Word boundary ensures "Uruguay" is not caught.
_YOUTH = re.compile(r'\bU\d{2}\b', re.IGNORECASE)
```

- [ ] **Step 4: Update `_parse_fixtures` to accept a `league` dict**

Replace the existing `_parse_fixtures` method with:

```python
def _parse_fixtures(self, fixtures: list[dict], league: dict) -> list[Match]:
    matches = []
    for f in fixtures:
        fixture = f.get("fixture", {})
        teams = f.get("teams", {})
        goals = f.get("goals", {})
        label = (
            f"{teams['home']['name']} {goals.get('home', 0)}–"
            f"{goals.get('away', 0)} {teams['away']['name']} | "
            f"{league['name']} {league['season']}"
        )
        matches.append(Match(
            match_id="apf:" + str(fixture["id"]),
            label=label,
            home_team=teams["home"]["name"],
            away_team=teams["away"]["name"],
            home_score=int(goals.get("home") or 0),
            away_score=int(goals.get("away") or 0),
            date=str(fixture.get("date", ""))[:10],
            competition=league["name"],
            season=str(league["season"]),
            country="International",
            is_live=True,
            is_warmup=league["is_warmup"],
        ))
    return matches
```

- [ ] **Step 5: Update `get_matches` to loop over `_LEAGUES` and apply the youth filter**

Replace the existing `get_matches` method with:

```python
def get_matches(self) -> list[Match]:
    all_matches = []
    for league in _LEAGUES:
        try:
            data = self._get("fixtures", {"league": league["id"], "season": league["season"]})
            fixtures = [
                f for f in data.get("response", [])
                if f.get("fixture", {}).get("status", {}).get("short") == "FT"
                and not _YOUTH.search(f.get("teams", {}).get("home", {}).get("name", ""))
                and not _YOUTH.search(f.get("teams", {}).get("away", {}).get("name", ""))
            ]
            all_matches.extend(self._parse_fixtures(fixtures, league))
        except Exception as e:
            logging.warning("Failed to fetch league %s: %s", league["id"], e)
    all_matches.sort(key=lambda m: m.date, reverse=True)
    return all_matches
```

- [ ] **Step 6: Run the full test suite**

```bash
python -m pytest backend/tests/ -v
```

Expected: all tests pass including the two new ones.

- [ ] **Step 7: Commit**

```bash
git add backend/providers/world_cup.py backend/tests/test_world_cup_provider.py
git commit -m "feat: add international friendlies to WorldCupProvider with youth match filter"
```

---

## Task 4: Show WARM-UP badge in MatchSelector

**Files:**
- Modify: `frontend/components/MatchSelector.tsx`

- [ ] **Step 1: Update the competitions `useMemo` to carry `is_warmup`**

Find this block in `MatchSelector.tsx`:

```tsx
const competitions = useMemo(() => {
  const map = new Map<string, { competition: string; country: string; is_live: boolean }>();
  for (const m of matches) {
    if (!map.has(m.competition)) {
      map.set(m.competition, { competition: m.competition, country: m.country, is_live: m.is_live });
    }
  }
```

Replace it with:

```tsx
const competitions = useMemo(() => {
  const map = new Map<string, { competition: string; country: string; is_live: boolean; is_warmup: boolean }>();
  for (const m of matches) {
    if (!map.has(m.competition)) {
      map.set(m.competition, { competition: m.competition, country: m.country, is_live: m.is_live, is_warmup: m.is_warmup });
    }
  }
```

- [ ] **Step 2: Replace the hardcoded LIVE badge with a conditional badge**

Find this line in the live competitions render:

```tsx
<span className="text-[10px] font-bold text-[#e94560] border border-[#e94560] px-1.5 py-0.5 rounded">LIVE</span>
```

Replace with:

```tsx
{c.is_warmup
  ? <span className="text-[10px] font-bold text-orange-400 border border-orange-400 px-1.5 py-0.5 rounded">WARM-UP</span>
  : <span className="text-[10px] font-bold text-[#e94560] border border-[#e94560] px-1.5 py-0.5 rounded">LIVE</span>
}
```

- [ ] **Step 3: Verify the frontend compiles**

```bash
cd "/Users/nahidmuzammil/Documents/Claude/Projects/Analysis app/frontend"
npm run build 2>&1 | tail -20
```

Expected: `✓ Compiled successfully` with no TypeScript errors.

- [ ] **Step 4: Commit**

```bash
cd "/Users/nahidmuzammil/Documents/Claude/Projects/Analysis app"
git add frontend/components/MatchSelector.tsx
git commit -m "feat: show WARM-UP badge for international friendly matches in match selector"
```

---

## Task 5: Single-command dev server

**Files:**
- Modify: `frontend/package.json`

- [ ] **Step 1: Install `concurrently`**

```bash
cd "/Users/nahidmuzammil/Documents/Claude/Projects/Analysis app/frontend"
npm install --save-dev concurrently
```

Expected: `added 1 package` (or similar), no errors.

- [ ] **Step 2: Add the `dev:all` script to `package.json`**

The `scripts` block should become:

```json
"scripts": {
  "dev": "next dev",
  "dev:all": "concurrently --kill-others --names 'API,UI' --prefix-colors 'blue,green' \"cd .. && uvicorn backend.main:app --reload --port 8000\" \"next dev\"",
  "build": "next build",
  "start": "next start",
  "lint": "next lint"
},
```

`--kill-others` means Ctrl+C stops both processes cleanly. `--names` and `--prefix-colors` label each output line so you know which server printed it.

- [ ] **Step 3: Verify the script exists and `concurrently` is in devDependencies**

```bash
cd "/Users/nahidmuzammil/Documents/Claude/Projects/Analysis app/frontend"
cat package.json | python3 -c "import sys,json; p=json.load(sys.stdin); print('dev:all' in p['scripts'], 'concurrently' in p.get('devDependencies', {}))"
```

Expected: `True True`

- [ ] **Step 4: Commit**

```bash
cd "/Users/nahidmuzammil/Documents/Claude/Projects/Analysis app"
git add frontend/package.json frontend/package-lock.json
git commit -m "feat: add dev:all script to start backend and frontend with one command"
```

---

## Manual Test Checklist

After all tasks are complete:

1. Start both servers: `cd frontend && npm run dev:all`
2. Open `http://localhost:3000`
3. Confirm "International Friendlies" appears in the **Live** section with an orange **WARM-UP** badge
4. Select a friendly match, pick a team, click Open Analysis
5. Confirm visualizations generate (Match Stats, Player Ratings, xG Timeline)
6. Confirm World Cup section shows a red **LIVE** badge (once WC starts June 11)
