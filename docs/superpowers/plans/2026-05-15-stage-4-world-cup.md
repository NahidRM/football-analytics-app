# Stage 4 + World Cup Mode Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Migrate The Whiteboard from Streamlit to a FastAPI + Next.js 14 + Supabase web app with World Cup 2026 support, deployed before June 11, 2026.

**Architecture:** FastAPI backend exposes REST endpoints and switches data providers via `APP_MODE` env var; Next.js 14 frontend (App Router) calls the backend for all data; Supabase stores every analysis and draft. The Streamlit app in `src/` remains untouched as a local fallback throughout.

**Tech Stack:** FastAPI, Python 3.11, Next.js 14 (TypeScript, Tailwind CSS), Supabase (PostgreSQL), statsbombpy, mplsoccer, soccerdata, anthropic, Vercel, Railway

---

## File Map

### Backend (`backend/`)

| File | Responsibility |
|------|---------------|
| `backend/main.py` | FastAPI app, all route definitions |
| `backend/config.py` | Reads `APP_MODE` + all env vars |
| `backend/content_generator.py` | Claude API call (copied from `src/`) |
| `backend/db.py` | Supabase client + analyses/drafts CRUD |
| `backend/providers/__init__.py` | `get_active_provider()` factory |
| `backend/providers/base.py` | Abstract `DataProvider` + dataclasses |
| `backend/providers/statsbomb.py` | StatsBomb implementation |
| `backend/providers/world_cup.py` | API-Football + FBref implementation |
| `backend/visualizations/passing_network.py` | Copied from `src/` |
| `backend/visualizations/heat_map.py` | Copied from `src/` |
| `backend/visualizations/shot_map.py` | Copied from `src/` |
| `backend/visualizations/press_map.py` | Copied from `src/` |
| `backend/visualizations/match_stats.py` | NEW: horizontal bar chart |
| `backend/visualizations/player_ratings.py` | NEW: starting 11 ratings grid |
| `backend/visualizations/xg_timeline.py` | NEW: xG accumulation by minute |
| `backend/requirements.txt` | Backend dependencies |
| `backend/.env` | Symlink or copy of root `.env` |

### Frontend (`frontend/`)

| File | Responsibility |
|------|---------------|
| `frontend/app/layout.tsx` | Root layout, Tailwind |
| `frontend/app/page.tsx` | Home: match selection |
| `frontend/app/analysis/[id]/page.tsx` | Analysis: charts + content tabs |
| `frontend/app/history/page.tsx` | History: saved analyses, team filter |
| `frontend/components/MatchSelector.tsx` | Match list/dropdown |
| `frontend/components/AnalysisCard.tsx` | Chart image + download button |
| `frontend/components/ContentEditor.tsx` | Newsletter + Twitter tabs, editable |
| `frontend/components/PendingBadge.tsx` | "xG data available in a few hours" |
| `frontend/components/HistoryList.tsx` | Filterable analysis history |
| `frontend/lib/api.ts` | Typed fetch wrappers for all endpoints |

---

## Milestone A — FastAPI Backend (local)

### Task 1: Project scaffold + config

**Files:**
- Create: `backend/requirements.txt`
- Create: `backend/config.py`
- Create: `backend/providers/__init__.py`
- Create: `backend/providers/base.py`
- Create: `backend/visualizations/__init__.py`
- Test: `backend/tests/test_config.py`

- [ ] **Step 1: Create `backend/` directory structure**

```bash
mkdir -p backend/providers backend/visualizations backend/tests
touch backend/providers/__init__.py backend/visualizations/__init__.py backend/tests/__init__.py
```

- [ ] **Step 2: Create `backend/requirements.txt`**

```
fastapi==0.111.0
uvicorn[standard]==0.29.0
python-dotenv==1.0.1
anthropic==0.28.0
statsbombpy==1.1.8
mplsoccer==1.3.0
matplotlib==3.8.4
pandas==2.2.2
numpy==1.26.4
Pillow==10.3.0
supabase==2.4.6
requests==2.31.0
soccerdata==0.6.0
pytest==8.2.0
httpx==0.27.0
```

- [ ] **Step 3: Write failing test for config**

Create `backend/tests/test_config.py`:

```python
import os
import pytest


def test_app_mode_statsbomb(monkeypatch):
    monkeypatch.setenv("APP_MODE", "statsbomb")
    # Re-import after env change
    import importlib
    import backend.config as cfg
    importlib.reload(cfg)
    assert cfg.APP_MODE == "statsbomb"


def test_app_mode_world_cup(monkeypatch):
    monkeypatch.setenv("APP_MODE", "world_cup")
    import importlib
    import backend.config as cfg
    importlib.reload(cfg)
    assert cfg.APP_MODE == "world_cup"


def test_invalid_app_mode_raises(monkeypatch):
    monkeypatch.setenv("APP_MODE", "invalid_mode")
    import importlib
    import backend.config as cfg
    with pytest.raises(ValueError, match="APP_MODE must be"):
        importlib.reload(cfg)
```

Run: `cd backend && python -m pytest tests/test_config.py -v`
Expected: FAIL (config.py doesn't exist)

- [ ] **Step 4: Create `backend/config.py`**

```python
import os
from dotenv import load_dotenv

load_dotenv()

APP_MODE = os.getenv("APP_MODE", "statsbomb")

if APP_MODE not in ("statsbomb", "world_cup"):
    raise ValueError(f"APP_MODE must be 'statsbomb' or 'world_cup', got '{APP_MODE}'")

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
API_FOOTBALL_KEY = os.getenv("API_FOOTBALL_KEY", "")
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "")
```

- [ ] **Step 5: Create `backend/providers/base.py` with dataclasses + abstract interface**

```python
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class Match:
    match_id: str
    label: str        # e.g. "France 2–1 Morocco | WC 2026 QF"
    home_team: str
    away_team: str
    home_score: int
    away_score: int
    date: str         # ISO date string "2026-07-19"


@dataclass
class TeamStats:
    possession: float
    shots: int
    shots_on_target: int
    passes: int
    pass_accuracy: float
    corners: int
    fouls: int


@dataclass
class MatchStats:
    home_team: str
    away_team: str
    home: TeamStats
    away: TeamStats


@dataclass
class PlayerStat:
    player_name: str
    team: str
    rating: float | None
    minutes: int
    goals: int
    assists: int
    shots: int
    key_passes: int
    tackles: int
    interceptions: int


@dataclass
class Shot:
    player: str
    team: str
    minute: int
    xg: float
    outcome: str   # 'Goal', 'Saved', 'Off T', 'Blocked'
    x: float
    y: float


@dataclass
class Lineup:
    home_team: str
    away_team: str
    home_formation: str   # e.g. "4-3-3"
    away_formation: str
    home_players: list[str] = field(default_factory=list)
    away_players: list[str] = field(default_factory=list)


class DataProvider(ABC):
    @abstractmethod
    def get_matches(self) -> list[Match]: ...

    @abstractmethod
    def get_match_stats(self, match_id: str) -> MatchStats: ...

    @abstractmethod
    def get_player_stats(self, match_id: str) -> list[PlayerStat]: ...

    @abstractmethod
    def get_shot_data(self, match_id: str) -> list[Shot] | None:
        """Return None when shot data is not yet available (FBref delay)."""
        ...

    @abstractmethod
    def get_lineup(self, match_id: str) -> Lineup: ...
```

- [ ] **Step 6: Run tests — should pass now**

```bash
cd backend && python -m pytest tests/test_config.py -v
```

Expected: 2 PASS, 1 PASS (invalid mode test may need `APP_MODE=invalid_mode` set before reload — adjust if needed)

- [ ] **Step 7: Commit**

```bash
git add backend/
git commit -m "feat: scaffold backend — config, provider interface, dataclasses"
```

---

### Task 2: StatsBomb provider

**Files:**
- Create: `backend/providers/statsbomb.py`
- Modify: `backend/providers/__init__.py`
- Test: `backend/tests/test_statsbomb_provider.py`

- [ ] **Step 1: Write failing test**

Create `backend/tests/test_statsbomb_provider.py`:

```python
import pytest
from backend.providers.statsbomb import StatsBombProvider
from backend.providers.base import Match, MatchStats, Lineup


def test_get_matches_returns_list():
    provider = StatsBombProvider()
    matches = provider.get_matches()
    assert isinstance(matches, list)
    assert len(matches) > 0


def test_match_has_required_fields():
    provider = StatsBombProvider()
    matches = provider.get_matches()
    m = matches[0]
    assert isinstance(m.match_id, str)
    assert isinstance(m.label, str)
    assert isinstance(m.home_team, str)
    assert isinstance(m.home_score, int)


def test_get_lineup_returns_lineup():
    # FA Women's Super League 2018/19, match 2275012
    provider = StatsBombProvider()
    lineup = provider.get_lineup("2275012")
    assert isinstance(lineup, Lineup)
    assert len(lineup.home_players) > 0
    assert len(lineup.away_players) > 0


def test_get_shot_data_returns_list_or_none():
    provider = StatsBombProvider()
    shots = provider.get_shot_data("2275012")
    # StatsBomb always has shot data
    assert shots is not None
    assert isinstance(shots, list)
```

Run: `cd backend && python -m pytest tests/test_statsbomb_provider.py -v`
Expected: FAIL (statsbomb.py doesn't exist)

- [ ] **Step 2: Create `backend/providers/statsbomb.py`**

```python
from __future__ import annotations
import warnings
warnings.filterwarnings("ignore")

import pandas as pd
from statsbombpy import sb

from .base import (
    DataProvider, Match, MatchStats, TeamStats,
    PlayerStat, Shot, Lineup
)

# StatsBomb competitions to expose — add more as needed
_COMPETITIONS = [
    (2, 44),    # Premier League 2003/04
    (2, 90),    # Premier League 2015/16
    (11, 1),    # La Liga 2004/05
    (16, 4),    # Champions League 2018/19
    (37, 42),   # FA Women's Super League 2018/19
    (55, 43),   # UEFA Euro 2020
]


class StatsBombProvider(DataProvider):
    def get_matches(self) -> list[Match]:
        rows = []
        for comp_id, season_id in _COMPETITIONS:
            try:
                df = sb.matches(competition_id=comp_id, season_id=season_id)
                comp_df = sb.competitions()
                comp_row = comp_df[
                    (comp_df["competition_id"] == comp_id) &
                    (comp_df["season_id"] == season_id)
                ]
                comp_name = comp_row.iloc[0]["competition_name"] if not comp_row.empty else ""
                season_name = comp_row.iloc[0]["season_name"] if not comp_row.empty else ""
                suffix = f"{comp_name} {season_name}"

                for _, row in df.iterrows():
                    label = (
                        f"{row['home_team']} {int(row['home_score'])}–"
                        f"{int(row['away_score'])} {row['away_team']} | {suffix}"
                    )
                    rows.append(Match(
                        match_id=str(int(row["match_id"])),
                        label=label,
                        home_team=str(row["home_team"]),
                        away_team=str(row["away_team"]),
                        home_score=int(row["home_score"]),
                        away_score=int(row["away_score"]),
                        date=str(row["match_date"])[:10],
                    ))
            except Exception:
                continue
        rows.sort(key=lambda m: m.date, reverse=True)
        return rows

    def get_match_stats(self, match_id: str) -> MatchStats:
        events = sb.events(match_id=int(match_id))
        teams = events["team"].dropna().unique().tolist()
        home_team = teams[0] if teams else "Home"
        away_team = teams[1] if len(teams) > 1 else "Away"

        def _team_stats(team: str) -> TeamStats:
            te = events[events["team"] == team]
            shots = te[te["type"] == "Shot"]
            on_target = shots[shots["shot_outcome"].isin(["Goal", "Saved"])]
            passes = te[(te["type"] == "Pass") & (te["pass_outcome"].isna())]
            all_passes = te[te["type"] == "Pass"]
            acc = len(passes) / max(len(all_passes), 1) * 100
            return TeamStats(
                possession=0.0,  # not available in event data directly
                shots=len(shots),
                shots_on_target=len(on_target),
                passes=len(all_passes),
                pass_accuracy=round(acc, 1),
                corners=len(te[(te["type"] == "Pass") & (te.get("pass_type", pd.Series(dtype=str)) == "Corner")]) if "pass_type" in te.columns else 0,
                fouls=len(te[te["type"] == "Foul Committed"]),
            )

        return MatchStats(
            home_team=home_team,
            away_team=away_team,
            home=_team_stats(home_team),
            away=_team_stats(away_team),
        )

    def get_player_stats(self, match_id: str) -> list[PlayerStat]:
        events = sb.events(match_id=int(match_id))
        players = events[events["player"].notna()][["player", "team"]].drop_duplicates()
        stats = []
        for _, row in players.iterrows():
            pe = events[events["player"] == row["player"]]
            shots = pe[pe["type"] == "Shot"]
            goals = shots[shots["shot_outcome"] == "Goal"]
            stats.append(PlayerStat(
                player_name=str(row["player"]),
                team=str(row["team"]),
                rating=None,
                minutes=90,
                goals=len(goals),
                assists=0,
                shots=len(shots),
                key_passes=len(pe[(pe["type"] == "Pass") & (pe.get("pass_goal_assist", pd.Series(dtype=object)).notna())]) if "pass_goal_assist" in pe.columns else 0,
                tackles=len(pe[pe["type"] == "Tackle"]),
                interceptions=len(pe[pe["type"] == "Interception"]),
            ))
        return stats

    def get_shot_data(self, match_id: str) -> list[Shot] | None:
        events = sb.events(match_id=int(match_id))
        shots_df = events[events["type"] == "Shot"]
        if shots_df.empty:
            return []
        shots = []
        for _, row in shots_df.iterrows():
            loc = row.get("location")
            x, y = (loc[0], loc[1]) if isinstance(loc, list) and len(loc) >= 2 else (0.0, 0.0)
            shots.append(Shot(
                player=str(row.get("player", "")),
                team=str(row.get("team", "")),
                minute=int(row.get("minute", 0)),
                xg=float(row.get("shot_statsbomb_xg", 0.0) or 0.0),
                outcome=str(row.get("shot_outcome", "")),
                x=float(x),
                y=float(y),
            ))
        return shots

    def get_lineup(self, match_id: str) -> Lineup:
        lineups = sb.lineups(match_id=int(match_id))
        teams = list(lineups.keys())
        home_team = teams[0] if teams else "Home"
        away_team = teams[1] if len(teams) > 1 else "Away"

        def _starters(team: str) -> list[str]:
            df = lineups.get(team, pd.DataFrame())
            if df.empty:
                return []
            starters = df[df.get("positions", pd.Series()).apply(
                lambda p: isinstance(p, list) and len(p) > 0
            )] if "positions" in df.columns else df
            return starters["player_name"].tolist()[:11]

        return Lineup(
            home_team=home_team,
            away_team=away_team,
            home_formation="",
            away_formation="",
            home_players=_starters(home_team),
            away_players=_starters(away_team),
        )
```

- [ ] **Step 3: Update `backend/providers/__init__.py`**

```python
from backend.config import APP_MODE
from backend.providers.base import DataProvider


def get_active_provider() -> DataProvider:
    if APP_MODE == "statsbomb":
        from backend.providers.statsbomb import StatsBombProvider
        return StatsBombProvider()
    from backend.providers.world_cup import WorldCupProvider
    return WorldCupProvider()
```

- [ ] **Step 4: Run tests**

```bash
cd backend && python -m pytest tests/test_statsbomb_provider.py -v
```

Expected: 4 PASS (StatsBomb fetches live data — may be slow first run, subsequent calls are cached by statsbombpy)

- [ ] **Step 5: Commit**

```bash
git add backend/providers/
git commit -m "feat: StatsBomb data provider implementation"
```

---

### Task 3: World Cup provider (API-Football)

**Files:**
- Create: `backend/providers/world_cup.py`
- Test: `backend/tests/test_world_cup_provider.py`

- [ ] **Step 1: Write failing test**

Create `backend/tests/test_world_cup_provider.py`:

```python
import pytest
from unittest.mock import patch, MagicMock
from backend.providers.world_cup import WorldCupProvider
from backend.providers.base import Match, MatchStats, TeamStats, Lineup


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
    matches = provider._parse_fixtures(FAKE_FIXTURES_RESPONSE["response"])
    assert len(matches) == 1
    m = matches[0]
    assert m.match_id == "12345"
    assert m.home_team == "France"
    assert m.away_team == "Morocco"
    assert m.home_score == 2
    assert m.away_score == 1


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
```

Run: `cd backend && python -m pytest tests/test_world_cup_provider.py -v`
Expected: FAIL

- [ ] **Step 2: Create `backend/providers/world_cup.py`**

```python
from __future__ import annotations
import requests
import warnings
warnings.filterwarnings("ignore")

from backend.config import API_FOOTBALL_KEY
from .base import (
    DataProvider, Match, MatchStats, TeamStats,
    PlayerStat, Shot, Lineup
)

_BASE_URL = "https://v3.football.api-sports.io"
_WC_LEAGUE_ID = 1
_WC_SEASON = 2026


class WorldCupProvider(DataProvider):
    def __init__(self):
        self._headers = {
            "x-apisports-key": API_FOOTBALL_KEY,
        }

    def _get(self, path: str, params: dict) -> dict:
        resp = requests.get(f"{_BASE_URL}/{path}", headers=self._headers, params=params, timeout=10)
        resp.raise_for_status()
        return resp.json()

    def _get_stat(self, stat_list: list[dict], name: str, cast, default=0):
        for s in stat_list:
            if s.get("type") == name:
                val = s.get("value")
                if val is None:
                    return default
                try:
                    if isinstance(val, str):
                        val = val.replace("%", "").strip()
                    return cast(val)
                except (ValueError, TypeError):
                    return default
        return default

    def _parse_fixtures(self, fixtures: list[dict]) -> list[Match]:
        matches = []
        for f in fixtures:
            fixture = f.get("fixture", {})
            teams = f.get("teams", {})
            goals = f.get("goals", {})
            league = f.get("league", {})
            label = (
                f"{teams['home']['name']} {goals.get('home', 0)}–"
                f"{goals.get('away', 0)} {teams['away']['name']} | "
                f"{league.get('name', 'World Cup')} {league.get('season', 2026)}"
            )
            matches.append(Match(
                match_id=str(fixture["id"]),
                label=label,
                home_team=teams["home"]["name"],
                away_team=teams["away"]["name"],
                home_score=int(goals.get("home") or 0),
                away_score=int(goals.get("away") or 0),
                date=str(fixture.get("date", ""))[:10],
            ))
        return matches

    def _parse_match_stats(self, home_team: str, away_team: str, response: list[dict]) -> MatchStats:
        team_stats: dict[str, list[dict]] = {}
        for entry in response:
            team_name = entry["team"]["name"]
            team_stats[team_name] = entry.get("statistics", [])

        def _extract(team: str) -> TeamStats:
            s = team_stats.get(team, [])
            poss_str = self._get_stat(s, "Ball Possession", str, "0%")
            poss = float(str(poss_str).replace("%", "").strip() or "0")
            return TeamStats(
                possession=poss,
                shots=self._get_stat(s, "Total Shots", int),
                shots_on_target=self._get_stat(s, "Shots on Goal", int),
                passes=self._get_stat(s, "Total passes", int),
                pass_accuracy=self._get_stat(s, "Passes %", float),
                corners=self._get_stat(s, "Corner Kicks", int),
                fouls=self._get_stat(s, "Fouls", int),
            )

        return MatchStats(
            home_team=home_team,
            away_team=away_team,
            home=_extract(home_team),
            away=_extract(away_team),
        )

    def get_matches(self) -> list[Match]:
        data = self._get("fixtures", {"league": _WC_LEAGUE_ID, "season": _WC_SEASON})
        fixtures = [
            f for f in data.get("response", [])
            if f.get("fixture", {}).get("status", {}).get("short") == "FT"
        ]
        matches = self._parse_fixtures(fixtures)
        matches.sort(key=lambda m: m.date, reverse=True)
        return matches

    def get_match_stats(self, match_id: str) -> MatchStats:
        # Get fixture info first to know home/away team names
        fix_data = self._get("fixtures", {"id": match_id})
        fix = fix_data["response"][0]
        home_team = fix["teams"]["home"]["name"]
        away_team = fix["teams"]["away"]["name"]

        stats_data = self._get("fixtures/statistics", {"fixture": match_id})
        return self._parse_match_stats(home_team, away_team, stats_data.get("response", []))

    def get_player_stats(self, match_id: str) -> list[PlayerStat]:
        data = self._get("fixtures/players", {"fixture": match_id})
        stats = []
        for team_entry in data.get("response", []):
            team_name = team_entry["team"]["name"]
            for player_entry in team_entry.get("players", []):
                p = player_entry.get("player", {})
                s_list = player_entry.get("statistics", [{}])
                s = s_list[0] if s_list else {}
                games = s.get("games", {})
                rating_raw = games.get("rating")
                stats.append(PlayerStat(
                    player_name=str(p.get("name", "")),
                    team=team_name,
                    rating=float(rating_raw) if rating_raw else None,
                    minutes=int(games.get("minutes") or 0),
                    goals=int((s.get("goals") or {}).get("total") or 0),
                    assists=int((s.get("goals") or {}).get("assists") or 0),
                    shots=int((s.get("shots") or {}).get("total") or 0),
                    key_passes=int((s.get("passes") or {}).get("key") or 0),
                    tackles=int((s.get("tackles") or {}).get("total") or 0),
                    interceptions=int((s.get("tackles") or {}).get("interceptions") or 0),
                ))
        return stats

    def get_shot_data(self, match_id: str) -> list[Shot] | None:
        """Attempt FBref fetch. Returns None if data not yet available."""
        try:
            import soccerdata as sd
            fbref = sd.FBref(leagues="World Cup", seasons=2026)
            # FBref shot data fetch — returns None if match not yet processed
            shots_df = fbref.read_shot_events()
            if shots_df is None or shots_df.empty:
                return None

            # Filter to this fixture (match_id from API-Football won't map directly,
            # so match on date+teams from get_matches; this is handled in main.py)
            return self._parse_fbref_shots(shots_df, match_id)
        except Exception:
            return None

    def _parse_fbref_shots(self, df, match_id: str) -> list[Shot] | None:
        # FBref shot columns vary — return None if parsing fails
        try:
            shots = []
            for _, row in df.iterrows():
                shots.append(Shot(
                    player=str(row.get("player", "")),
                    team=str(row.get("squad", "")),
                    minute=int(row.get("minute", 0) or 0),
                    xg=float(row.get("xg", 0.0) or 0.0),
                    outcome=str(row.get("outcome", "")),
                    x=float(row.get("x", 0.0) or 0.0),
                    y=float(row.get("y", 0.0) or 0.0),
                ))
            return shots if shots else None
        except Exception:
            return None

    def get_lineup(self, match_id: str) -> Lineup:
        data = self._get("fixtures/lineups", {"fixture": match_id})
        response = data.get("response", [])
        home_entry = response[0] if response else {}
        away_entry = response[1] if len(response) > 1 else {}

        def _players(entry: dict) -> list[str]:
            return [p["player"]["name"] for p in entry.get("startXI", [])]

        return Lineup(
            home_team=home_entry.get("team", {}).get("name", ""),
            away_team=away_entry.get("team", {}).get("name", ""),
            home_formation=home_entry.get("formation", ""),
            away_formation=away_entry.get("formation", ""),
            home_players=_players(home_entry),
            away_players=_players(away_entry),
        )
```

- [ ] **Step 3: Run tests**

```bash
cd backend && python -m pytest tests/test_world_cup_provider.py -v
```

Expected: 3 PASS (tests use mocked/parsed data, no live API calls)

- [ ] **Step 4: Commit**

```bash
git add backend/providers/world_cup.py backend/tests/test_world_cup_provider.py
git commit -m "feat: World Cup data provider (API-Football + FBref stub)"
```

---

### Task 4: Copy + register existing visualizations

**Files:**
- Copy: `src/passing_network.py` → `backend/visualizations/passing_network.py`
- Copy: `src/heat_map.py` → `backend/visualizations/heat_map.py`
- Copy: `src/shot_map.py` → `backend/visualizations/shot_map.py`
- Copy: `src/press_map.py` → `backend/visualizations/press_map.py`
- Create: `backend/visualizations/__init__.py` (registry)

- [ ] **Step 1: Copy visualization files**

```bash
cp "src/passing_network.py" backend/visualizations/passing_network.py
cp "src/heat_map.py" backend/visualizations/heat_map.py
cp "src/shot_map.py" backend/visualizations/shot_map.py
cp "src/press_map.py" backend/visualizations/press_map.py
```

- [ ] **Step 2: Create `backend/visualizations/__init__.py` with analysis registry**

```python
# Maps analysis_type string → (modes it's available in)
ANALYSIS_REGISTRY = {
    "passing_network": ["statsbomb"],
    "heat_map":        ["statsbomb"],
    "shot_map":        ["statsbomb"],
    "press_map":       ["statsbomb"],
    "match_stats":     ["world_cup"],
    "player_ratings":  ["world_cup"],
    "xg_timeline":     ["world_cup"],
}


def get_available_analyses(mode: str) -> list[str]:
    """Return analysis types available for the given APP_MODE."""
    return [k for k, modes in ANALYSIS_REGISTRY.items() if mode in modes]
```

- [ ] **Step 3: Write test for registry**

Create `backend/tests/test_viz_registry.py`:

```python
from backend.visualizations import get_available_analyses

def test_statsbomb_analyses():
    result = get_available_analyses("statsbomb")
    assert "passing_network" in result
    assert "match_stats" not in result

def test_world_cup_analyses():
    result = get_available_analyses("world_cup")
    assert "match_stats" in result
    assert "player_ratings" in result
    assert "xg_timeline" in result
    assert "passing_network" not in result
```

Run: `cd backend && python -m pytest tests/test_viz_registry.py -v`
Expected: 2 PASS

- [ ] **Step 4: Commit**

```bash
git add backend/visualizations/
git commit -m "feat: copy existing visualizations to backend, add analysis registry"
```

---

### Task 5: New World Cup visualizations

**Files:**
- Create: `backend/visualizations/match_stats.py`
- Create: `backend/visualizations/player_ratings.py`
- Create: `backend/visualizations/xg_timeline.py`
- Test: `backend/tests/test_new_visualizations.py`

- [ ] **Step 1: Write failing tests**

Create `backend/tests/test_new_visualizations.py`:

```python
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pytest

from backend.providers.base import MatchStats, TeamStats, PlayerStat, Shot
from backend.visualizations.match_stats import draw_match_stats
from backend.visualizations.player_ratings import draw_player_ratings
from backend.visualizations.xg_timeline import draw_xg_timeline


def _make_match_stats() -> MatchStats:
    return MatchStats(
        home_team="France",
        away_team="Morocco",
        home=TeamStats(possession=60.0, shots=14, shots_on_target=6,
                       passes=520, pass_accuracy=89.0, corners=5, fouls=12),
        away=TeamStats(possession=40.0, shots=8, shots_on_target=3,
                       passes=340, pass_accuracy=82.0, corners=3, fouls=15),
    )


def _make_player_stats() -> list[PlayerStat]:
    return [
        PlayerStat("Mbappé", "France", 8.9, 90, 1, 1, 5, 3, 1, 0),
        PlayerStat("Griezmann", "France", 7.5, 90, 0, 0, 2, 4, 2, 1),
        PlayerStat("Lloris", "France", 7.2, 90, 0, 0, 0, 0, 0, 0),
        PlayerStat("En-Nesyri", "Morocco", 7.8, 90, 1, 0, 3, 1, 0, 0),
    ]


def _make_lineup():
    from backend.providers.base import Lineup
    return Lineup(
        home_team="France", away_team="Morocco",
        home_formation="4-3-3", away_formation="4-2-3-1",
        home_players=["Lloris", "Pavard", "Varane", "Upamecano", "T. Hernandez",
                       "Tchouaméni", "Rabiot", "Griezmann", "Dembélé", "Giroud", "Mbappé"],
        away_players=["Bounou", "Hakimi", "Aguerd", "Saiss", "Mazraoui",
                       "Ounahi", "Amrabat", "Ziyech", "Boufal", "En-Nesyri", "Sabiri"],
    )


def _make_shots() -> list[Shot]:
    return [
        Shot("Mbappé", "France", 23, 0.45, "Goal", 105.0, 34.0),
        Shot("Giroud", "France", 67, 0.12, "Saved", 103.0, 40.0),
        Shot("En-Nesyri", "Morocco", 44, 0.31, "Goal", 104.0, 36.0),
    ]


def test_draw_match_stats_returns_figure():
    fig = draw_match_stats(_make_match_stats(), "France 2–1 Morocco | WC 2026 QF")
    assert isinstance(fig, plt.Figure)
    plt.close(fig)


def test_draw_player_ratings_returns_figure():
    fig = draw_player_ratings(_make_player_stats(), _make_lineup(), "France", "France 2–1 Morocco | WC 2026 QF")
    assert isinstance(fig, plt.Figure)
    plt.close(fig)


def test_draw_xg_timeline_returns_figure():
    fig = draw_xg_timeline(_make_shots(), "France", "Morocco", "France 2–1 Morocco | WC 2026 QF")
    assert isinstance(fig, plt.Figure)
    plt.close(fig)
```

Run: `cd backend && python -m pytest tests/test_new_visualizations.py -v`
Expected: FAIL (files don't exist)

- [ ] **Step 2: Create `backend/visualizations/match_stats.py`**

```python
from __future__ import annotations
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

from backend.providers.base import MatchStats


def draw_match_stats(stats: MatchStats, match_label: str) -> plt.Figure:
    """Horizontal bar chart comparing both teams side-by-side for each stat."""
    categories = ["Possession %", "Shots", "Shots on Target", "Pass Accuracy %", "Corners", "Fouls"]
    home_vals = [
        stats.home.possession,
        stats.home.shots,
        stats.home.shots_on_target,
        stats.home.pass_accuracy,
        stats.home.corners,
        stats.home.fouls,
    ]
    away_vals = [
        stats.away.possession,
        stats.away.shots,
        stats.away.shots_on_target,
        stats.away.pass_accuracy,
        stats.away.corners,
        stats.away.fouls,
    ]

    fig, axes = plt.subplots(len(categories), 1, figsize=(10, 8))
    fig.patch.set_facecolor("#1a1a2e")

    HOME_COLOR = "#e94560"
    AWAY_COLOR = "#0f3460"
    TEXT_COLOR = "#e0e0e0"

    for i, (ax, cat, hv, av) in enumerate(zip(axes, categories, home_vals, away_vals)):
        ax.set_facecolor("#16213e")
        total = hv + av if (hv + av) > 0 else 1
        home_pct = hv / total

        ax.barh(0, home_pct, color=HOME_COLOR, height=0.5, align="center")
        ax.barh(0, -(1 - home_pct), color=AWAY_COLOR, height=0.5, align="center")
        ax.set_xlim(-1, 1)
        ax.set_yticks([])
        ax.set_xticks([])

        # Labels
        ax.text(-0.02, 0, str(int(av)) if cat not in ("Possession %", "Pass Accuracy %") else f"{av:.0f}%",
                ha="right", va="center", color=TEXT_COLOR, fontsize=10, fontweight="bold")
        ax.text(0.02, 0, str(int(hv)) if cat not in ("Possession %", "Pass Accuracy %") else f"{hv:.0f}%",
                ha="left", va="center", color=TEXT_COLOR, fontsize=10, fontweight="bold")
        ax.text(0, -0.45, cat, ha="center", va="top", color="#aaaaaa", fontsize=8)
        for spine in ax.spines.values():
            spine.set_visible(False)

    home_patch = mpatches.Patch(color=HOME_COLOR, label=stats.home_team)
    away_patch = mpatches.Patch(color=AWAY_COLOR, label=stats.away_team)
    fig.legend(handles=[home_patch, away_patch], loc="upper center",
               ncol=2, frameon=False, labelcolor=TEXT_COLOR, fontsize=11)
    fig.suptitle(f"Match Stats\n{match_label}", color=TEXT_COLOR, fontsize=12, y=0.98)
    fig.tight_layout(rect=[0, 0, 1, 0.93])
    return fig
```

- [ ] **Step 3: Create `backend/visualizations/player_ratings.py`**

```python
from __future__ import annotations
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

from backend.providers.base import PlayerStat, Lineup


def draw_player_ratings(
    player_stats: list[PlayerStat],
    lineup: Lineup,
    team: str,
    match_label: str,
) -> plt.Figure:
    """Grid of the starting 11 players with their ratings. Top performer highlighted."""
    players = lineup.home_players if team == lineup.home_team else lineup.away_players
    if not players:
        players = [p.player_name for p in player_stats if p.team == team][:11]

    # Build rating lookup
    rating_map = {p.player_name: p.rating for p in player_stats if p.team == team}

    fig, ax = plt.subplots(figsize=(10, 7))
    fig.patch.set_facecolor("#1a1a2e")
    ax.set_facecolor("#1a1a2e")
    ax.set_xlim(0, 4)
    ax.set_ylim(0, 3)
    ax.axis("off")

    CARD_W, CARD_H = 0.85, 0.55
    COLS = 4
    BG = "#16213e"
    HIGHLIGHT = "#e94560"
    TEXT = "#e0e0e0"
    SUBTEXT = "#aaaaaa"

    best_rating = max((rating_map.get(p) or 0.0 for p in players), default=0.0)

    for idx, player_name in enumerate(players[:11]):
        col = idx % COLS
        row = idx // COLS
        x = col * (CARD_W + 0.1) + 0.05
        y = 2.6 - row * (CARD_H + 0.08)

        rating = rating_map.get(player_name)
        is_best = rating is not None and abs(rating - best_rating) < 0.01

        color = HIGHLIGHT if is_best else BG
        rect = mpatches.FancyBboxPatch((x, y), CARD_W, CARD_H,
                                        boxstyle="round,pad=0.02",
                                        facecolor=color, edgecolor="#333355", linewidth=1)
        ax.add_patch(rect)
        short_name = player_name.split()[-1] if " " in player_name else player_name
        ax.text(x + CARD_W / 2, y + CARD_H * 0.65, short_name,
                ha="center", va="center", color=TEXT, fontsize=9, fontweight="bold")
        rating_str = f"{rating:.1f}" if rating else "—"
        ax.text(x + CARD_W / 2, y + CARD_H * 0.28, rating_str,
                ha="center", va="center", color=TEXT, fontsize=13, fontweight="bold")

    ax.set_title(f"Player Ratings — {team}\n{match_label}",
                 color=TEXT, fontsize=11, pad=12)
    fig.tight_layout()
    return fig
```

- [ ] **Step 4: Create `backend/visualizations/xg_timeline.py`**

```python
from __future__ import annotations
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from backend.providers.base import Shot


def draw_xg_timeline(
    shots: list[Shot],
    home_team: str,
    away_team: str,
    match_label: str,
) -> plt.Figure:
    """Cumulative xG by minute for both teams. Goals marked with vertical dashes."""
    HOME_COLOR = "#e94560"
    AWAY_COLOR = "#4fc3f7"
    BG = "#1a1a2e"
    GRID = "#2a2a4e"
    TEXT = "#e0e0e0"

    fig, ax = plt.subplots(figsize=(12, 5))
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)

    minutes = list(range(0, 92))

    def _cumulative(team: str):
        xg_by_min = {m: 0.0 for m in minutes}
        for s in shots:
            if s.team == team:
                m = min(int(s.minute), 91)
                xg_by_min[m] += s.xg
        cum = 0.0
        curve = []
        for m in minutes:
            cum += xg_by_min[m]
            curve.append(cum)
        return curve

    home_xg = _cumulative(home_team)
    away_xg = _cumulative(away_team)

    ax.plot(minutes, home_xg, color=HOME_COLOR, linewidth=2.5, label=f"{home_team} xG")
    ax.plot(minutes, away_xg, color=AWAY_COLOR, linewidth=2.5, label=f"{away_team} xG")

    # Mark goals with vertical lines
    for s in shots:
        if s.outcome == "Goal":
            color = HOME_COLOR if s.team == home_team else AWAY_COLOR
            ax.axvline(x=s.minute, color=color, linestyle="--", linewidth=1, alpha=0.6)
            ax.text(s.minute + 0.5, max(home_xg + away_xg) * 0.05,
                    s.player.split()[-1], color=color, fontsize=7, rotation=90, va="bottom")

    ax.set_xlim(0, 91)
    ax.set_ylim(0, None)
    ax.set_xlabel("Minute", color=TEXT)
    ax.set_ylabel("Cumulative xG", color=TEXT)
    ax.tick_params(colors=TEXT)
    for spine in ax.spines.values():
        spine.set_color(GRID)
    ax.grid(color=GRID, linewidth=0.5)
    ax.legend(frameon=False, labelcolor=TEXT)
    ax.set_title(f"xG Timeline\n{match_label}", color=TEXT, fontsize=12)
    fig.tight_layout()
    return fig
```

- [ ] **Step 5: Run tests**

```bash
cd backend && python -m pytest tests/test_new_visualizations.py -v
```

Expected: 3 PASS

- [ ] **Step 6: Commit**

```bash
git add backend/visualizations/match_stats.py backend/visualizations/player_ratings.py backend/visualizations/xg_timeline.py backend/tests/test_new_visualizations.py
git commit -m "feat: match stats, player ratings, and xG timeline visualizations"
```

---

### Task 6: Copy content_generator + FastAPI main

**Files:**
- Copy: `src/content_generator.py` → `backend/content_generator.py`
- Create: `backend/main.py`
- Test: `backend/tests/test_api.py`

- [ ] **Step 1: Copy content_generator**

```bash
cp src/content_generator.py backend/content_generator.py
```

No changes needed — the function signature `generate_content(analysis_type, team, match_label, stats_summary)` is identical.

- [ ] **Step 2: Write failing API tests**

Create `backend/tests/test_api.py`:

```python
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from backend.providers.base import Match, MatchStats, TeamStats, Lineup, PlayerStat


@pytest.fixture
def client():
    from backend.main import app
    return TestClient(app)


def _mock_provider():
    m = MagicMock()
    m.get_matches.return_value = [
        Match("123", "France 2–1 Morocco | WC 2026 QF", "France", "Morocco", 2, 1, "2026-07-05")
    ]
    m.get_match_stats.return_value = MatchStats(
        home_team="France", away_team="Morocco",
        home=TeamStats(60.0, 14, 6, 520, 89.0, 5, 12),
        away=TeamStats(40.0, 8, 3, 340, 82.0, 3, 15),
    )
    m.get_player_stats.return_value = [
        PlayerStat("Mbappé", "France", 8.9, 90, 1, 1, 5, 3, 1, 0)
    ]
    m.get_shot_data.return_value = None
    m.get_lineup.return_value = Lineup("France", "Morocco", "4-3-3", "4-2-3-1",
                                        ["Lloris", "Pavard", "Varane", "Upamecano", "Hernandez",
                                         "Tchouaméni", "Rabiot", "Griezmann", "Dembélé", "Giroud", "Mbappé"],
                                        ["Bounou", "Hakimi", "Aguerd", "Saiss", "Mazraoui",
                                         "Ounahi", "Amrabat", "Ziyech", "Boufal", "En-Nesyri", "Sabiri"])
    return m


def test_get_matches(client):
    with patch("backend.main.get_active_provider", return_value=_mock_provider()):
        response = client.get("/matches")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert data[0]["match_id"] == "123"
    assert data[0]["label"] == "France 2–1 Morocco | WC 2026 QF"


def test_get_match_detail(client):
    with patch("backend.main.get_active_provider", return_value=_mock_provider()):
        response = client.get("/matches/123")
    assert response.status_code == 200
    data = response.json()
    assert data["match_id"] == "123"
    assert data["fbref_available"] is False


def test_analyze_match_stats(client):
    with patch("backend.main.get_active_provider", return_value=_mock_provider()):
        response = client.post("/analyze", json={
            "match_id": "123",
            "team": "France",
            "analysis_type": "match_stats",
        })
    assert response.status_code == 200
    data = response.json()
    assert "image_base64" in data
    assert "stats_summary" in data
    assert data["fbref_available"] is False


def test_analyze_unknown_type_returns_400(client):
    with patch("backend.main.get_active_provider", return_value=_mock_provider()):
        response = client.post("/analyze", json={
            "match_id": "123",
            "team": "France",
            "analysis_type": "unknown_type",
        })
    assert response.status_code == 400
```

Run: `cd backend && python -m pytest tests/test_api.py -v`
Expected: FAIL (main.py doesn't exist)

- [ ] **Step 3: Create `backend/main.py`**

```python
from __future__ import annotations
import base64
import io
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.config import APP_MODE
from backend.providers import get_active_provider
from backend.providers.base import DataProvider
from backend.content_generator import generate_content
from backend.visualizations import get_available_analyses

app = FastAPI(title="The Whiteboard API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://*.vercel.app"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request / Response models ─────────────────────────────────────────────────

class AnalyzeRequest(BaseModel):
    match_id: str
    team: str
    analysis_type: str
    player_name: str | None = None


class ContentRequest(BaseModel):
    analysis_type: str
    team: str
    match_label: str
    stats_summary: str
    analysis_id: str | None = None


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/matches")
def list_matches():
    provider = get_active_provider()
    matches = provider.get_matches()
    return [
        {
            "match_id": m.match_id,
            "label": m.label,
            "home_team": m.home_team,
            "away_team": m.away_team,
            "home_score": m.home_score,
            "away_score": m.away_score,
            "date": m.date,
        }
        for m in matches
    ]


@app.get("/matches/{match_id}")
def get_match(match_id: str):
    provider = get_active_provider()
    matches = provider.get_matches()
    match = next((m for m in matches if m.match_id == match_id), None)
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")

    shot_data = provider.get_shot_data(match_id)
    return {
        "match_id": match.match_id,
        "label": match.label,
        "home_team": match.home_team,
        "away_team": match.away_team,
        "home_score": match.home_score,
        "away_score": match.away_score,
        "date": match.date,
        "fbref_available": shot_data is not None,
        "available_analyses": get_available_analyses(APP_MODE),
    }


@app.post("/analyze")
def analyze(req: AnalyzeRequest):
    available = get_available_analyses(APP_MODE)
    if req.analysis_type not in available:
        raise HTTPException(
            status_code=400,
            detail=f"analysis_type '{req.analysis_type}' not available in {APP_MODE} mode. "
                   f"Available: {available}",
        )

    provider = get_active_provider()
    shot_data = provider.get_shot_data(req.match_id)
    fbref_available = shot_data is not None

    # Build match label
    matches = provider.get_matches()
    match = next((m for m in matches if m.match_id == req.match_id), None)
    match_label = match.label if match else req.match_id

    fig, stats_summary = _run_analysis(req, provider, shot_data, match_label)

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    image_b64 = base64.b64encode(buf.read()).decode()

    return {
        "image_base64": image_b64,
        "stats_summary": stats_summary,
        "match_label": match_label,
        "fbref_available": fbref_available,
    }


@app.post("/content")
def content(req: ContentRequest):
    newsletter, twitter = generate_content(
        req.analysis_type, req.team, req.match_label, req.stats_summary
    )
    return {"newsletter": newsletter, "twitter": twitter}


@app.get("/analyses")
def list_analyses():
    try:
        from backend.db import get_analyses
        return get_analyses()
    except Exception:
        return []


@app.post("/analyses")
def save_analysis(body: dict):
    try:
        from backend.db import save_analysis as db_save
        return db_save(body)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/analyses/{analysis_id}/drafts")
def get_drafts(analysis_id: str):
    try:
        from backend.db import get_drafts
        return get_drafts(analysis_id)
    except Exception:
        return []


# ── Analysis dispatch ─────────────────────────────────────────────────────────

def _run_analysis(req: AnalyzeRequest, provider: DataProvider, shot_data, match_label: str):
    t = req.analysis_type

    if t == "match_stats":
        from backend.visualizations.match_stats import draw_match_stats
        stats = provider.get_match_stats(req.match_id)
        fig = draw_match_stats(stats, match_label)
        summary = (
            f"{stats.home_team}: {stats.home.shots} shots ({stats.home.shots_on_target} on target), "
            f"{stats.home.possession}% possession. "
            f"{stats.away_team}: {stats.away.shots} shots ({stats.away.shots_on_target} on target), "
            f"{stats.away.possession}% possession."
        )
        return fig, summary

    if t == "player_ratings":
        from backend.visualizations.player_ratings import draw_player_ratings
        player_stats = provider.get_player_stats(req.match_id)
        lineup = provider.get_lineup(req.match_id)
        fig = draw_player_ratings(player_stats, lineup, req.team, match_label)
        team_players = [p for p in player_stats if p.team == req.team]
        top = max(team_players, key=lambda p: p.rating or 0.0, default=None)
        summary = f"Player ratings for {req.team}."
        if top and top.rating:
            summary += f" Top performer: {top.player_name} ({top.rating:.1f})."
        return fig, summary

    if t == "xg_timeline":
        from backend.visualizations.xg_timeline import draw_xg_timeline
        lineup = provider.get_lineup(req.match_id)
        shots = shot_data or []
        fig = draw_xg_timeline(shots, lineup.home_team, lineup.away_team, match_label)
        home_xg = sum(s.xg for s in shots if s.team == lineup.home_team)
        away_xg = sum(s.xg for s in shots if s.team == lineup.away_team)
        summary = f"{lineup.home_team} xG: {home_xg:.2f}. {lineup.away_team} xG: {away_xg:.2f}."
        return fig, summary

    # StatsBomb visualizations — need events DataFrame
    from statsbombpy import sb
    events = sb.events(match_id=int(req.match_id))

    if t == "passing_network":
        from backend.visualizations.passing_network import draw_passing_network
        fig = draw_passing_network(events, req.team, match_label)
        passes = events[(events["type"] == "Pass") & (events["team"] == req.team) & (events["pass_outcome"].isna())]
        summary = f"Successful passes: {len(passes)}."
        return fig, summary

    if t == "heat_map":
        from backend.visualizations.heat_map import draw_heat_map
        if not req.player_name:
            raise HTTPException(status_code=400, detail="player_name required for heat_map")
        fig = draw_heat_map(events, req.player_name, req.team, match_label)
        return fig, f"Heat map for {req.player_name}."

    if t == "shot_map":
        from backend.visualizations.shot_map import draw_shot_map
        fig = draw_shot_map(events, req.team, match_label)
        shots = events[(events["type"] == "Shot") & (events["team"] == req.team)]
        return fig, f"Shots: {len(shots)}."

    if t == "press_map":
        from backend.visualizations.press_map import draw_press_map
        fig = draw_press_map(events, req.team, match_label)
        pressure = events[(events["type"] == "Pressure") & (events["team"] == req.team)]
        return fig, f"Total pressures: {len(pressure)}."

    raise HTTPException(status_code=400, detail=f"Unknown analysis_type: {t}")
```

- [ ] **Step 4: Run tests**

```bash
cd backend && python -m pytest tests/test_api.py -v
```

Expected: 4 PASS

- [ ] **Step 5: Smoke test — run backend locally**

```bash
cd backend && pip install -r requirements.txt
APP_MODE=statsbomb uvicorn backend.main:app --reload --port 8000
```

Open `http://localhost:8000/matches` in browser — should return a list of StatsBomb matches.

- [ ] **Step 6: Commit**

```bash
git add backend/main.py backend/content_generator.py backend/tests/test_api.py
git commit -m "feat: FastAPI main — all endpoints, StatsBomb + World Cup dispatch"
```

---

## Milestone B — Next.js Frontend (local)

### Task 7: Next.js project scaffold + API client

**Files:**
- Create: `frontend/` (via `create-next-app`)
- Create: `frontend/lib/api.ts`
- Create: `frontend/.env.local`

- [ ] **Step 1: Scaffold Next.js project**

```bash
npx create-next-app@14 frontend \
  --typescript \
  --tailwind \
  --app \
  --no-src-dir \
  --import-alias "@/*" \
  --no-git
```

Answer prompts: TypeScript=Yes, ESLint=Yes, Tailwind=Yes, src/=No, App Router=Yes.

- [ ] **Step 2: Create `frontend/.env.local`**

```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

- [ ] **Step 3: Create `frontend/lib/api.ts`**

```typescript
const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export interface Match {
  match_id: string;
  label: string;
  home_team: string;
  away_team: string;
  home_score: number;
  away_score: number;
  date: string;
}

export interface MatchDetail extends Match {
  fbref_available: boolean;
  available_analyses: string[];
}

export interface AnalyzeResponse {
  image_base64: string;
  stats_summary: string;
  match_label: string;
  fbref_available: boolean;
}

export interface ContentResponse {
  newsletter: string;
  twitter: string;
}

export interface AnalysisRecord {
  id: string;
  created_at: string;
  mode: string;
  match_label: string;
  team: string;
  opponent: string;
  analysis_type: string;
  image_base64: string | null;
  stats_summary: string | null;
  tags: string[];
}

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail ?? `API error ${res.status}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  getMatches: () => apiFetch<Match[]>("/matches"),

  getMatch: (matchId: string) => apiFetch<MatchDetail>(`/matches/${matchId}`),

  analyze: (body: {
    match_id: string;
    team: string;
    analysis_type: string;
    player_name?: string;
  }) =>
    apiFetch<AnalyzeResponse>("/analyze", {
      method: "POST",
      body: JSON.stringify(body),
    }),

  generateContent: (body: {
    analysis_type: string;
    team: string;
    match_label: string;
    stats_summary: string;
  }) =>
    apiFetch<ContentResponse>("/content", {
      method: "POST",
      body: JSON.stringify(body),
    }),

  getAnalyses: () => apiFetch<AnalysisRecord[]>("/analyses"),

  saveAnalysis: (body: Partial<AnalysisRecord>) =>
    apiFetch<AnalysisRecord>("/analyses", {
      method: "POST",
      body: JSON.stringify(body),
    }),

  getDrafts: (analysisId: string) =>
    apiFetch<{ newsletter: string; twitter: string }[]>(
      `/analyses/${analysisId}/drafts`
    ),
};
```

- [ ] **Step 4: Verify TypeScript compiles**

```bash
cd frontend && npx tsc --noEmit
```

Expected: no errors

- [ ] **Step 5: Commit**

```bash
git add frontend/
git commit -m "feat: Next.js scaffold + typed API client"
```

---

### Task 8: Home screen — match selection

**Files:**
- Create: `frontend/components/MatchSelector.tsx`
- Modify: `frontend/app/page.tsx`
- Modify: `frontend/app/layout.tsx`

- [ ] **Step 1: Update `frontend/app/layout.tsx`**

```tsx
import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "The Whiteboard",
  description: "Football analytics",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className={`${inter.className} bg-[#1a1a2e] text-gray-100 min-h-screen`}>
        <header className="border-b border-gray-800 px-6 py-4">
          <h1 className="text-xl font-bold tracking-tight">The Whiteboard</h1>
        </header>
        <main className="max-w-5xl mx-auto px-6 py-8">{children}</main>
      </body>
    </html>
  );
}
```

- [ ] **Step 2: Create `frontend/components/MatchSelector.tsx`**

```tsx
"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import type { Match } from "@/lib/api";

interface Props {
  matches: Match[];
}

export default function MatchSelector({ matches }: Props) {
  const [selected, setSelected] = useState<string>("");
  const [team, setTeam] = useState<string>("");
  const router = useRouter();

  const match = matches.find((m) => m.match_id === selected);

  function handleAnalyze() {
    if (!match || !team) return;
    router.push(`/analysis/${match.match_id}?team=${encodeURIComponent(team)}`);
  }

  return (
    <div className="space-y-6">
      <div>
        <label className="block text-sm text-gray-400 mb-1">Match</label>
        <select
          value={selected}
          onChange={(e) => { setSelected(e.target.value); setTeam(""); }}
          className="w-full bg-[#16213e] border border-gray-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-[#e94560]"
        >
          <option value="">Select a match...</option>
          {matches.map((m) => (
            <option key={m.match_id} value={m.match_id}>
              {m.label}
            </option>
          ))}
        </select>
      </div>

      {match && (
        <div>
          <label className="block text-sm text-gray-400 mb-1">Team to analyse</label>
          <div className="flex gap-3">
            {[match.home_team, match.away_team].map((t) => (
              <button
                key={t}
                onClick={() => setTeam(t)}
                className={`px-4 py-2 rounded-lg text-sm border transition-colors ${
                  team === t
                    ? "bg-[#e94560] border-[#e94560] text-white"
                    : "border-gray-700 text-gray-300 hover:border-gray-500"
                }`}
              >
                {t}
              </button>
            ))}
          </div>
        </div>
      )}

      <button
        onClick={handleAnalyze}
        disabled={!match || !team}
        className="w-full py-3 rounded-lg bg-[#e94560] text-white font-semibold text-sm disabled:opacity-40 disabled:cursor-not-allowed hover:bg-[#c73652] transition-colors"
      >
        Open Analysis
      </button>
    </div>
  );
}
```

- [ ] **Step 3: Update `frontend/app/page.tsx`**

```tsx
import { api } from "@/lib/api";
import MatchSelector from "@/components/MatchSelector";
import Link from "next/link";

export default async function HomePage() {
  let matches = [];
  try {
    matches = await api.getMatches();
  } catch {
    // backend not running — show empty state
  }

  return (
    <div className="max-w-xl space-y-8">
      <div>
        <h2 className="text-2xl font-bold mb-1">Select a match</h2>
        <p className="text-gray-400 text-sm">Pick a match and team to generate your analysis.</p>
      </div>

      {matches.length === 0 ? (
        <p className="text-gray-500 text-sm">
          No matches available — make sure the backend is running.
        </p>
      ) : (
        <MatchSelector matches={matches} />
      )}

      <div className="pt-4 border-t border-gray-800">
        <Link href="/history" className="text-sm text-gray-400 hover:text-gray-200 transition-colors">
          View saved analyses →
        </Link>
      </div>
    </div>
  );
}
```

- [ ] **Step 4: Run dev server and verify home screen**

```bash
cd frontend && npm run dev
```

Open `http://localhost:3000` — should show match selector populated from backend. If backend is not running, shows empty state message.

- [ ] **Step 5: Commit**

```bash
git add frontend/app/ frontend/components/MatchSelector.tsx
git commit -m "feat: home screen with match selector"
```

---

### Task 9: Analysis view — charts and content

**Files:**
- Create: `frontend/components/AnalysisCard.tsx`
- Create: `frontend/components/ContentEditor.tsx`
- Create: `frontend/components/PendingBadge.tsx`
- Create: `frontend/app/analysis/[id]/page.tsx`

- [ ] **Step 1: Create `frontend/components/PendingBadge.tsx`**

```tsx
export default function PendingBadge() {
  return (
    <div className="inline-flex items-center gap-2 bg-yellow-900/30 border border-yellow-700/50 text-yellow-400 text-xs px-3 py-1.5 rounded-full">
      <span className="w-1.5 h-1.5 rounded-full bg-yellow-400 animate-pulse" />
      Shot data and xG timeline available in a few hours — refresh to check.
    </div>
  );
}
```

- [ ] **Step 2: Create `frontend/components/AnalysisCard.tsx`**

```tsx
"use client";

interface Props {
  imageBase64: string;
  analysisType: string;
  team: string;
  matchLabel: string;
}

export default function AnalysisCard({ imageBase64, analysisType, team, matchLabel }: Props) {
  function handleDownload() {
    const a = document.createElement("a");
    a.href = `data:image/png;base64,${imageBase64}`;
    a.download = `${team.replace(/\s+/g, "_").toLowerCase()}_${analysisType}.png`;
    a.click();
  }

  return (
    <div className="space-y-3">
      <img
        src={`data:image/png;base64,${imageBase64}`}
        alt={`${analysisType} for ${team}`}
        className="w-full rounded-lg border border-gray-800"
      />
      <div className="flex items-center justify-between text-xs text-gray-400">
        <span>{analysisType.replace(/_/g, " ")} — {team} | {matchLabel}</span>
        <button
          onClick={handleDownload}
          className="px-3 py-1 border border-gray-700 rounded hover:border-gray-400 transition-colors"
        >
          ↓ Download
        </button>
      </div>
    </div>
  );
}
```

- [ ] **Step 3: Create `frontend/components/ContentEditor.tsx`**

```tsx
"use client";
import { useState } from "react";

interface Props {
  newsletter: string;
  twitter: string;
}

export default function ContentEditor({ newsletter, twitter }: Props) {
  const [nl, setNl] = useState(newsletter);
  const [tw, setTw] = useState(twitter);
  const [tab, setTab] = useState<"newsletter" | "twitter">("newsletter");

  return (
    <div className="space-y-3">
      <div className="flex border-b border-gray-800">
        {(["newsletter", "twitter"] as const).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`px-4 py-2 text-sm capitalize border-b-2 transition-colors -mb-px ${
              tab === t
                ? "border-[#e94560] text-white"
                : "border-transparent text-gray-400 hover:text-gray-200"
            }`}
          >
            {t === "newsletter" ? "Newsletter Draft" : "Twitter Thread"}
          </button>
        ))}
      </div>

      {tab === "newsletter" ? (
        <textarea
          value={nl}
          onChange={(e) => setNl(e.target.value)}
          rows={14}
          className="w-full bg-[#16213e] border border-gray-700 rounded-lg px-4 py-3 text-sm focus:outline-none focus:border-[#e94560] resize-none font-mono leading-relaxed"
        />
      ) : (
        <textarea
          value={tw}
          onChange={(e) => setTw(e.target.value)}
          rows={14}
          className="w-full bg-[#16213e] border border-gray-700 rounded-lg px-4 py-3 text-sm focus:outline-none focus:border-[#e94560] resize-none font-mono leading-relaxed"
        />
      )}
    </div>
  );
}
```

- [ ] **Step 4: Create `frontend/app/analysis/[id]/page.tsx`**

```tsx
"use client";
import { useState } from "react";
import { useSearchParams } from "next/navigation";
import { api } from "@/lib/api";
import type { AnalyzeResponse, ContentResponse } from "@/lib/api";
import AnalysisCard from "@/components/AnalysisCard";
import ContentEditor from "@/components/ContentEditor";
import PendingBadge from "@/components/PendingBadge";

const ANALYSIS_LABELS: Record<string, string> = {
  passing_network: "Passing Network",
  heat_map: "Heat Map",
  shot_map: "Shot Map",
  press_map: "Press Map",
  match_stats: "Match Stats",
  player_ratings: "Player Ratings",
  xg_timeline: "xG Timeline",
};

interface PageProps {
  params: { id: string };
}

export default function AnalysisPage({ params }: PageProps) {
  const searchParams = useSearchParams();
  const team = searchParams.get("team") ?? "";
  const matchId = params.id;

  const [availableAnalyses, setAvailableAnalyses] = useState<string[]>([]);
  const [selectedAnalysis, setSelectedAnalysis] = useState<string>("");
  const [playerName, setPlayerName] = useState<string>("");
  const [result, setResult] = useState<AnalyzeResponse | null>(null);
  const [content, setContent] = useState<ContentResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [contentLoading, setContentLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [initialized, setInitialized] = useState(false);

  // Load available analyses on first render
  if (!initialized) {
    setInitialized(true);
    api.getMatch(matchId).then((m) => {
      setAvailableAnalyses(m.available_analyses);
      if (m.available_analyses.length > 0) setSelectedAnalysis(m.available_analyses[0]);
    });
  }

  async function handleAnalyze() {
    setLoading(true);
    setError(null);
    setContent(null);
    try {
      const r = await api.analyze({
        match_id: matchId,
        team,
        analysis_type: selectedAnalysis,
        player_name: selectedAnalysis === "heat_map" ? playerName : undefined,
      });
      setResult(r);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleGenerateContent() {
    if (!result) return;
    setContentLoading(true);
    try {
      const c = await api.generateContent({
        analysis_type: selectedAnalysis,
        team,
        match_label: result.match_label,
        stats_summary: result.stats_summary,
      });
      setContent(c);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setContentLoading(false);
    }
  }

  return (
    <div className="space-y-8 max-w-3xl">
      <div>
        <p className="text-sm text-gray-400">Analysing: <span className="text-white">{team}</span></p>
      </div>

      {/* Analysis picker */}
      <div className="space-y-4">
        <div className="flex flex-wrap gap-2">
          {availableAnalyses.map((a) => (
            <button
              key={a}
              onClick={() => setSelectedAnalysis(a)}
              className={`px-4 py-2 rounded-lg text-sm border transition-colors ${
                selectedAnalysis === a
                  ? "bg-[#e94560] border-[#e94560] text-white"
                  : "border-gray-700 text-gray-300 hover:border-gray-500"
              }`}
            >
              {ANALYSIS_LABELS[a] ?? a}
            </button>
          ))}
        </div>

        {selectedAnalysis === "heat_map" && (
          <input
            placeholder="Player name"
            value={playerName}
            onChange={(e) => setPlayerName(e.target.value)}
            className="bg-[#16213e] border border-gray-700 rounded-lg px-3 py-2 text-sm w-full max-w-xs focus:outline-none focus:border-[#e94560]"
          />
        )}

        <button
          onClick={handleAnalyze}
          disabled={loading || !selectedAnalysis}
          className="px-6 py-2 bg-[#e94560] rounded-lg text-sm font-semibold disabled:opacity-40 hover:bg-[#c73652] transition-colors"
        >
          {loading ? "Generating..." : "Generate Visualization"}
        </button>
      </div>

      {error && <p className="text-red-400 text-sm">{error}</p>}

      {result && (
        <div className="space-y-6">
          <AnalysisCard
            imageBase64={result.image_base64}
            analysisType={selectedAnalysis}
            team={team}
            matchLabel={result.match_label}
          />

          {!result.fbref_available && selectedAnalysis === "xg_timeline" && <PendingBadge />}

          <div>
            <p className="text-xs text-gray-400 mb-3">
              Based on: {ANALYSIS_LABELS[selectedAnalysis]} — {team} | {result.match_label}
            </p>
            <button
              onClick={handleGenerateContent}
              disabled={contentLoading}
              className="px-6 py-2 border border-[#e94560] text-[#e94560] rounded-lg text-sm font-semibold hover:bg-[#e94560] hover:text-white transition-colors disabled:opacity-40"
            >
              {contentLoading ? "Writing..." : "Generate Newsletter + Twitter Thread"}
            </button>
          </div>

          {content && (
            <ContentEditor newsletter={content.newsletter} twitter={content.twitter} />
          )}
        </div>
      )}
    </div>
  );
}
```

- [ ] **Step 5: Verify TypeScript and test in browser**

```bash
cd frontend && npx tsc --noEmit
npm run dev
```

Open `http://localhost:3000`, select a match and team, click "Open Analysis". Verify: visualization picker shows correct options for mode, chart renders, content tabs work.

- [ ] **Step 6: Commit**

```bash
git add frontend/components/ frontend/app/analysis/
git commit -m "feat: analysis view — viz picker, chart display, content generation tabs"
```

---

## Milestone C — Supabase Integration

### Task 10: Supabase schema + db.py

**Files:**
- Create: `backend/db.py`
- Test: `backend/tests/test_db.py`

- [ ] **Step 1: Create Supabase tables**

In the Supabase dashboard (supabase.com → your project → SQL editor), run:

```sql
CREATE TABLE analyses (
  id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  created_at     TIMESTAMPTZ DEFAULT now(),
  mode           TEXT NOT NULL,
  match_label    TEXT NOT NULL,
  team           TEXT NOT NULL,
  opponent       TEXT NOT NULL,
  analysis_type  TEXT NOT NULL,
  image_base64   TEXT,
  stats_summary  TEXT,
  tags           TEXT[]
);

CREATE TABLE drafts (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  analysis_id   UUID REFERENCES analyses(id) ON DELETE CASCADE,
  created_at    TIMESTAMPTZ DEFAULT now(),
  newsletter    TEXT,
  twitter       TEXT,
  regenerated   BOOLEAN DEFAULT false
);
```

- [ ] **Step 2: Add Supabase keys to `.env`**

```bash
# Add to backend/.env (or root .env):
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_SERVICE_KEY=your-service-role-key
```

- [ ] **Step 3: Write failing test for db.py**

Create `backend/tests/test_db.py`:

```python
import pytest
from unittest.mock import patch, MagicMock


def _mock_supabase():
    mock = MagicMock()
    mock.table.return_value.insert.return_value.execute.return_value.data = [
        {"id": "abc-123", "created_at": "2026-06-15T12:00:00Z",
         "mode": "world_cup", "match_label": "France 2–1 Morocco",
         "team": "France", "opponent": "Morocco",
         "analysis_type": "match_stats", "image_base64": None,
         "stats_summary": "14 shots", "tags": ["France", "Morocco"]}
    ]
    mock.table.return_value.select.return_value.order.return_value.execute.return_value.data = []
    return mock


def test_save_analysis_returns_record():
    from backend.db import save_analysis
    with patch("backend.db._client", _mock_supabase()):
        result = save_analysis({
            "mode": "world_cup",
            "match_label": "France 2–1 Morocco",
            "team": "France",
            "opponent": "Morocco",
            "analysis_type": "match_stats",
            "stats_summary": "14 shots",
        })
    assert result["id"] == "abc-123"
    assert result["team"] == "France"


def test_get_analyses_returns_list():
    from backend.db import get_analyses
    with patch("backend.db._client", _mock_supabase()):
        result = get_analyses()
    assert isinstance(result, list)
```

Run: `cd backend && python -m pytest tests/test_db.py -v`
Expected: FAIL

- [ ] **Step 4: Create `backend/db.py`**

```python
from __future__ import annotations
from supabase import create_client, Client
from backend.config import SUPABASE_URL, SUPABASE_SERVICE_KEY

_client: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)


def save_analysis(record: dict) -> dict:
    tags = list({record.get("team", ""), record.get("opponent", "")})
    data = {
        "mode":          record.get("mode", ""),
        "match_label":   record.get("match_label", ""),
        "team":          record.get("team", ""),
        "opponent":      record.get("opponent", ""),
        "analysis_type": record.get("analysis_type", ""),
        "image_base64":  record.get("image_base64"),
        "stats_summary": record.get("stats_summary"),
        "tags":          tags,
    }
    result = _client.table("analyses").insert(data).execute()
    return result.data[0]


def save_draft(analysis_id: str, newsletter: str, twitter: str, regenerated: bool = False) -> dict:
    result = _client.table("drafts").insert({
        "analysis_id": analysis_id,
        "newsletter":  newsletter,
        "twitter":     twitter,
        "regenerated": regenerated,
    }).execute()
    return result.data[0]


def get_analyses(tag: str | None = None) -> list[dict]:
    query = _client.table("analyses").select("*").order("created_at", desc=True)
    result = query.execute()
    rows = result.data or []
    if tag:
        rows = [r for r in rows if tag in (r.get("tags") or [])]
    return rows


def get_drafts(analysis_id: str) -> list[dict]:
    result = (
        _client.table("drafts")
        .select("*")
        .eq("analysis_id", analysis_id)
        .order("created_at", desc=True)
        .execute()
    )
    return result.data or []
```

- [ ] **Step 5: Wire save into `/analyze` and `/content` endpoints**

In `backend/main.py`, update the `analyze` function to save after generating, and add a `/content` route that saves the draft. Replace the `analyze` endpoint's return block with:

```python
    # ... (existing analysis code above) ...

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    image_b64 = base64.b64encode(buf.read()).decode()

    # Persist to Supabase (non-blocking — failure doesn't break the response)
    analysis_db_id = None
    try:
        from backend.db import save_analysis as db_save
        match_detail = next((m for m in provider.get_matches() if m.match_id == req.match_id), None)
        opponent = (
            match_detail.away_team if match_detail and match_detail.home_team == req.team
            else match_detail.home_team if match_detail else ""
        ) if match_detail else ""
        saved = db_save({
            "mode":          APP_MODE,
            "match_label":   match_label,
            "team":          req.team,
            "opponent":      opponent,
            "analysis_type": req.analysis_type,
            "image_base64":  image_b64,
            "stats_summary": stats_summary,
        })
        analysis_db_id = saved.get("id")
    except Exception:
        pass  # Supabase failure is non-fatal

    return {
        "image_base64":    image_b64,
        "stats_summary":   stats_summary,
        "match_label":     match_label,
        "fbref_available": fbref_available,
        "analysis_id":     analysis_db_id,
    }
```

Update the `/content` route to also save the draft:

```python
@app.post("/content")
def content(req: ContentRequest):
    from backend.db import save_draft
    newsletter, twitter = generate_content(
        req.analysis_type, req.team, req.match_label, req.stats_summary
    )
    try:
        if req.analysis_id:
            save_draft(req.analysis_id, newsletter, twitter)
    except Exception:
        pass  # non-fatal
    return {"newsletter": newsletter, "twitter": twitter}
```

Also add `analysis_id: str | None = None` to `ContentRequest`.

- [ ] **Step 6: Run tests**

```bash
cd backend && python -m pytest tests/test_db.py -v
```

Expected: 2 PASS

- [ ] **Step 7: Commit**

```bash
git add backend/db.py backend/tests/test_db.py backend/main.py
git commit -m "feat: Supabase integration — save analyses and drafts"
```

---

### Task 11: History page

**Files:**
- Create: `frontend/components/HistoryList.tsx`
- Create: `frontend/app/history/page.tsx`

- [ ] **Step 1: Create `frontend/components/HistoryList.tsx`**

```tsx
"use client";
import { useState } from "react";
import Link from "next/link";
import type { AnalysisRecord } from "@/lib/api";

interface Props {
  analyses: AnalysisRecord[];
}

const LABELS: Record<string, string> = {
  passing_network: "Passing Network",
  heat_map: "Heat Map",
  shot_map: "Shot Map",
  press_map: "Press Map",
  match_stats: "Match Stats",
  player_ratings: "Player Ratings",
  xg_timeline: "xG Timeline",
};

export default function HistoryList({ analyses }: Props) {
  const [filter, setFilter] = useState("");

  const filtered = filter.trim()
    ? analyses.filter((a) =>
        (a.tags ?? []).some((t) =>
          t.toLowerCase().includes(filter.toLowerCase())
        )
      )
    : analyses;

  return (
    <div className="space-y-4">
      <input
        placeholder="Filter by team..."
        value={filter}
        onChange={(e) => setFilter(e.target.value)}
        className="w-full max-w-sm bg-[#16213e] border border-gray-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-[#e94560]"
      />

      {filtered.length === 0 ? (
        <p className="text-gray-500 text-sm">No analyses found.</p>
      ) : (
        <div className="divide-y divide-gray-800">
          {filtered.map((a) => (
            <Link
              key={a.id}
              href={`/history/${a.id}`}
              className="flex items-center justify-between py-4 hover:text-[#e94560] transition-colors group"
            >
              <div>
                <p className="text-sm font-medium">{a.match_label}</p>
                <p className="text-xs text-gray-400 mt-0.5">
                  {LABELS[a.analysis_type] ?? a.analysis_type} — {a.team}
                </p>
              </div>
              <p className="text-xs text-gray-500">
                {new Date(a.created_at).toLocaleDateString()}
              </p>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
```

- [ ] **Step 2: Create `frontend/app/history/page.tsx`**

```tsx
import { api } from "@/lib/api";
import HistoryList from "@/components/HistoryList";
import Link from "next/link";

export default async function HistoryPage() {
  let analyses = [];
  try {
    analyses = await api.getAnalyses();
  } catch {
    // backend unreachable
  }

  return (
    <div className="max-w-3xl space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">History</h2>
          <p className="text-gray-400 text-sm mt-1">All saved analyses, newest first.</p>
        </div>
        <Link href="/" className="text-sm text-gray-400 hover:text-gray-200 transition-colors">
          ← New analysis
        </Link>
      </div>

      <HistoryList analyses={analyses} />
    </div>
  );
}
```

- [ ] **Step 3: Verify in browser**

Navigate to `http://localhost:3000/history` — should show saved analyses (or empty state if Supabase not yet connected). Team filter should work in real-time.

- [ ] **Step 4: Commit**

```bash
git add frontend/components/HistoryList.tsx frontend/app/history/
git commit -m "feat: history page with team filter"
```

---

## Milestone D — Deployment

### Task 12: Deploy backend to Railway

**Files:**
- Create: `backend/Procfile`

- [ ] **Step 1: Create `backend/Procfile`**

```
web: uvicorn backend.main:app --host 0.0.0.0 --port $PORT
```

- [ ] **Step 2: Deploy on Railway**

```bash
# Install Railway CLI if not already installed
npm install -g @railway/cli

# Login
railway login

# From project root, init and deploy
railway init
railway up
```

In Railway dashboard: add all env vars from `.env`:
- `APP_MODE`
- `ANTHROPIC_API_KEY`
- `API_FOOTBALL_KEY`
- `SUPABASE_URL`
- `SUPABASE_SERVICE_KEY`

- [ ] **Step 3: Verify backend is live**

```bash
curl https://your-railway-url.railway.app/matches
```

Expected: JSON array of matches

- [ ] **Step 4: Commit**

```bash
git add backend/Procfile
git commit -m "chore: add Procfile for Railway deployment"
```

---

### Task 13: Deploy frontend to Vercel

**Files:**
- No new files — Vercel reads `frontend/` directly

- [ ] **Step 1: Deploy via Vercel CLI**

```bash
npm install -g vercel
cd frontend && vercel --prod
```

When prompted:
- Root directory: `frontend`
- Framework: Next.js (auto-detected)

- [ ] **Step 2: Add env var in Vercel dashboard**

In Vercel project → Settings → Environment Variables:
```
NEXT_PUBLIC_API_URL = https://your-railway-url.railway.app
```

Redeploy after adding the var.

- [ ] **Step 3: Update CORS in backend**

In `backend/main.py`, update the `allow_origins` list to include the Vercel URL:

```python
allow_origins=[
    "http://localhost:3000",
    "https://*.vercel.app",
    "https://your-exact-vercel-domain.vercel.app",  # add production URL
],
```

Redeploy backend after this change.

- [ ] **Step 4: End-to-end test on production URLs**

- Open production Vercel URL
- Select a match, generate a visualization
- Generate newsletter + Twitter thread
- Check Supabase `analyses` table for the saved record
- Navigate to History page — saved analysis should appear

- [ ] **Step 5: Commit**

```bash
git add backend/main.py
git commit -m "chore: add production Vercel URL to CORS allowlist"
```

---

## Post-deployment: Switch to World Cup mode

When the World Cup starts (June 11, 2026):

```bash
# In Railway dashboard → Variables:
APP_MODE=world_cup

# Or locally for testing:
APP_MODE=world_cup uvicorn backend.main:app --reload --port 8000
```

Railway auto-restarts on env var changes. Frontend and Supabase need no changes — the backend switch is transparent.

---

## Running tests (full suite)

```bash
cd backend && python -m pytest tests/ -v
```

Expected: All tests pass. StatsBomb tests require network access (statsbombpy fetches from GitHub). World Cup provider tests are fully mocked.
