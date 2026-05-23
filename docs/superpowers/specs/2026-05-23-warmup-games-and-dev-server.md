# Spec: Warm-Up Games + Single-Command Dev Server

**Date:** 2026-05-23
**Status:** Approved

## Goal

Surface international warm-up/friendly matches (API-Football league 10) in the app before FIFA World Cup 2026 starts on June 11, so the API-Football integration can be tested with real live data now. Also add a single-command dev server so both backend and frontend start together.

## Context

- API-Football Pro key is active until 2026-06-13, 7500 requests/day
- `WorldCupProvider` currently only fetches league ID 1 (World Cup) with season 2026
- League ID 10 ("Friendlies") contains senior international friendlies — confirmed live today (Mexico 2-0 Ghana, 2026-05-23)
- Youth matches (U17, U20, U21, U23 etc.) are mixed into league 10 and must be filtered out
- Running the app currently requires two terminals

---

## Section 1 — Data Model

**File:** `backend/providers/base.py`

Add one field to the `Match` dataclass:

```python
is_warmup: bool = False
```

Field semantics:

| Scenario | `is_live` | `is_warmup` |
|---|---|---|
| StatsBomb archive | `False` | `False` |
| International friendly | `True` | `True` |
| World Cup match (live) | `True` | `False` |

**File:** `frontend/lib/api.ts`

Add matching field to the `Match` TypeScript interface:

```typescript
is_warmup: boolean;
```

---

## Section 2 — Backend: WorldCupProvider

**File:** `backend/providers/world_cup.py`

### League config table

Replace `_WC_LEAGUE_ID = 1` and `_WC_SEASON = 2026` with:

```python
_LEAGUES = [
    {"id": 1,  "season": 2026, "name": "FIFA World Cup 2026",     "is_warmup": False},
    {"id": 10, "season": 2026, "name": "International Friendlies", "is_warmup": True},
]
```

### Youth filter

Add a compiled regex at the top of the file:

```python
import re
_YOUTH = re.compile(r'\bU\d{2}\b', re.IGNORECASE)
```

A fixture is skipped if either team name matches `_YOUTH` (e.g. "Hungary U17", "Tajikistan U20"). Word boundary ensures "Uruguay" is not blocked.

### `get_matches()` changes

Loop over `_LEAGUES`, fetch fixtures for each, apply youth filter, collect results:

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

### `_parse_fixtures()` changes

Accept a `league` config dict as a second argument and use it for `competition`, `is_live`, and `is_warmup`. Update the direct call in `backend/tests/test_world_cup_provider.py` to pass a league dict too.

```python
def _parse_fixtures(self, fixtures: list[dict], league: dict) -> list[Match]:
    ...
    matches.append(Match(
        ...
        competition=league["name"],
        season=str(league["season"]),
        country="International",
        is_live=True,
        is_warmup=league["is_warmup"],
    ))
```

### Config cleanup

**File:** `backend/config.py`

Remove the stale `APP_MODE` env var and its validation block — routing is now handled by match ID prefix (`sb:` / `apf:`), not a mode flag.

**File:** `backend/tests/test_config.py`

Remove the three `APP_MODE` tests that go with it (they test a validation that no longer exists).

---

## Section 3 — Frontend: Warm-Up Badge

**File:** `frontend/components/MatchSelector.tsx`

The competitions map needs to carry `is_warmup` alongside `is_live`:

```typescript
const map = new Map<string, { competition: string; country: string; is_live: boolean; is_warmup: boolean }>();
```

In the Live section, render the badge conditionally:

```tsx
{c.is_warmup
  ? <span className="text-[10px] font-bold text-orange-400 border border-orange-400 px-1.5 py-0.5 rounded">WARM-UP</span>
  : <span className="text-[10px] font-bold text-[#e94560] border border-[#e94560] px-1.5 py-0.5 rounded">LIVE</span>
}
```

No other UI changes — warm-up competitions still appear at the top of the list and navigate the same way as live matches.

---

## Section 4 — Single-Command Dev Server

**File:** `frontend/package.json`

Install `concurrently` as a dev dependency and add a `dev:all` script:

```json
"scripts": {
  "dev:all": "concurrently --names 'API,UI' --prefix-colors 'blue,green' \"cd .. && uvicorn backend.main:app --reload --port 8000\" \"next dev\""
}
```

Usage: `npm run dev:all` from the `frontend/` directory. Both servers boot in one terminal with colour-coded, labelled output.

---

## Out of Scope

- Caching for `WorldCupProvider` (live data should be fresh; no cache needed)
- `get_cached_match()` support for `apf:` prefix (already falls back to lineup data correctly)
- Live/in-progress match status (only finished matches `FT` are shown for analysis)
