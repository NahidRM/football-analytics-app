# Stage 4 + World Cup Mode — Design Spec

**Date:** 2026-05-15
**Replaces:** `docs/superpowers/plans/2026-05-12-stage-4-web-app.md`
**Status:** Approved

---

## Goal

Migrate The Whiteboard from Streamlit to a proper web app (Next.js + FastAPI + Supabase) with World Cup 2026 support built in from day one. The app must be usable for the World Cup, which starts June 11, 2026.

---

## Product Summary

The Whiteboard is a personal football analytics tool. After a match, Nahid selects it in the app, generates visualizations, and uses the Claude API to draft a newsletter piece and Twitter thread in his own voice. The app saves every analysis and draft to a personal history.

- **Users:** Nahid only. No auth, no sharing, no login.
- **Primary use case during World Cup:** Analyse a match within minutes of the final whistle, generate content for Twitter and Beehiiv.
- **Modes:** StatsBomb (historical EPL/UCL data) and World Cup (live API-Football + FBref).

---

## Architecture

### Layers

```
The Whiteboard
├── frontend/         Next.js 14 (App Router, TypeScript) — hosted on Vercel
├── backend/          FastAPI (Python) — hosted on Railway
└── database/         Supabase (PostgreSQL)
```

### How they connect

- Frontend calls backend REST endpoints for all data and visualizations
- Backend reads `APP_MODE` from `.env` and activates the correct data provider
- Backend writes to Supabase after every analysis and content generation
- Frontend reads from Supabase for history and saved drafts
- No direct frontend → Supabase calls (all go through backend — keeps credentials server-side only)

### Mode toggle

`APP_MODE` in `.env` controls which data provider is active:

```
APP_MODE=statsbomb    # historical mode (EPL, UCL, La Liga etc.)
APP_MODE=world_cup    # World Cup 2026 mode
```

This is a developer-level switch — changed once before the World Cup starts, not a UI toggle. Restart the backend after changing it.

---

## Backend Structure

```
backend/
├── main.py                    ← FastAPI app + all route definitions
├── config.py                  ← reads APP_MODE and all env vars
├── content_generator.py       ← unchanged from Stage 3
├── providers/
│   ├── __init__.py            ← exports get_active_provider()
│   ├── base.py                ← DataProvider abstract interface
│   ├── statsbomb.py           ← StatsBomb implementation
│   └── world_cup.py           ← API-Football + FBref implementation
├── visualizations/
│   ├── passing_network.py     ← unchanged from Stage 1
│   ├── heat_map.py            ← unchanged
│   ├── shot_map.py            ← unchanged (used in both modes)
│   ├── press_map.py           ← unchanged
│   ├── match_stats.py         ← NEW: horizontal bar chart (World Cup)
│   ├── player_ratings.py      ← NEW: starting 11 ratings grid (World Cup)
│   └── xg_timeline.py         ← NEW: xG accumulation by minute (World Cup)
├── db.py                      ← Supabase client + all DB operations
└── requirements.txt
```

### Data Provider Interface (`providers/base.py`)

Both providers implement this interface. FastAPI routes call these methods — they never import StatsBomb or API-Football directly.

```python
class DataProvider:
    def get_matches(self) -> list[Match]
    def get_match_stats(self, match_id) -> MatchStats
    def get_player_stats(self, match_id) -> list[PlayerStat]
    def get_shot_data(self, match_id) -> list[Shot] | None  # None = not yet available
    def get_lineup(self, match_id) -> Lineup
```

`get_shot_data()` returning `None` signals that FBref data is not yet available. The frontend handles this gracefully by showing a "pending" state on the xG timeline.

---

## World Cup Data Provider

### API-Football (immediate — available within minutes of final whistle)

- Fixtures for World Cup 2026 (FIFA World Cup league ID: 1, season: 2026)
- Match statistics: possession, shots, shots on target, passes, pass accuracy, corners, fouls, cards
- Player statistics per match: rating, minutes played, goals, assists, shots, key passes, tackles, interceptions
- Lineups: starting 11, formation string (e.g. "4-3-3")

### FBref via soccerdata (delayed — typically 2–6 hours after match)

- Shot-level data: player, minute, xG value, outcome, location coordinates
- Advanced player stats: progressive passes, pressures, PPDA, aerials won

### On-demand enrichment strategy

The backend does not poll or schedule. Every time a World Cup match is requested:
1. Return API-Football data immediately
2. Attempt FBref fetch in the same request
3. If FBref succeeds → merge and return full dataset, mark `fbref_available: true`
4. If FBref fails/returns empty → return API-Football data only, mark `fbref_available: false`

The frontend shows a subtle notice: *"Shot data and xG timeline available in a few hours — refresh to check."*

---

## API Endpoints (FastAPI)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/matches` | List of matches for selection (filtered by mode) |
| GET | `/matches/{match_id}` | Match detail: stats, lineups, availability flags |
| POST | `/analyze` | Run a visualization; returns PNG as base64 + stats summary |
| POST | `/content` | Call Claude API; return newsletter + twitter drafts |
| GET | `/analyses` | Saved analysis history from Supabase |
| POST | `/analyses` | Save an analysis record |
| GET | `/analyses/{id}/drafts` | Saved drafts for a given analysis |

### `/analyze` request body

```json
{
  "match_id": "...",
  "team": "France",
  "analysis_type": "match_stats | player_ratings | xg_timeline | passing_network | heat_map | shot_map | press_map",
  "player_name": "Mbappé"  // only for heat_map
}
```

### `/analyze` response

```json
{
  "image_base64": "...",
  "stats_summary": "...",
  "match_label": "France 2–1 Morocco | WC 2026 QF",
  "fbref_available": true
}
```

---

## Visualizations by Mode

### StatsBomb mode

| Chart | Status |
|-------|--------|
| Passing Network | Existing — moved to `backend/visualizations/` |
| Heat Map | Existing |
| Shot Map | Existing |
| Press Map | Existing |

### World Cup mode

| Chart | Data source | Available | Notes |
|-------|-------------|-----------|-------|
| Match Stats Comparison | API-Football | Immediately | Horizontal bar, both teams side by side |
| Player Ratings Grid | API-Football | Immediately | Starting 11, top performer highlighted |
| xG Timeline | FBref | ~2–6 hrs | Line chart: xG by minute, both teams |

Charts not available in the current mode are not shown in the UI — no greyed-out options.

---

## Database (Supabase)

### `analyses` table

```sql
CREATE TABLE analyses (
  id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  created_at     TIMESTAMPTZ DEFAULT now(),
  mode           TEXT NOT NULL,           -- 'statsbomb' or 'world_cup'
  match_label    TEXT NOT NULL,
  team           TEXT NOT NULL,           -- team being analysed
  opponent       TEXT NOT NULL,           -- the other team
  analysis_type  TEXT NOT NULL,
  image_base64   TEXT,
  stats_summary  TEXT,
  tags           TEXT[]                   -- e.g. ['France', 'Morocco']
);
```

`tags` stores both team names so filtering "all France matches" returns analyses where France was either the analysed team or the opponent.

### `drafts` table

```sql
CREATE TABLE drafts (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  analysis_id   UUID REFERENCES analyses(id) ON DELETE CASCADE,
  created_at    TIMESTAMPTZ DEFAULT now(),
  newsletter    TEXT,
  twitter       TEXT,
  regenerated   BOOLEAN DEFAULT false
);
```

Drafts are linked to analyses. Multiple drafts per analysis are allowed — each regeneration creates a new row rather than overwriting.

---

## Frontend Structure

```
frontend/
├── app/
│   ├── page.tsx                  ← match selection home screen
│   ├── analysis/
│   │   └── [id]/page.tsx         ← analysis view: charts + content tabs
│   ├── history/
│   │   └── page.tsx              ← saved analyses, filterable by team
│   └── layout.tsx
├── components/
│   ├── MatchSelector.tsx         ← dropdown/list for picking a match
│   ├── AnalysisCard.tsx          ← chart image + download button
│   ├── ContentEditor.tsx         ← newsletter + twitter tabs, editable
│   ├── PendingBadge.tsx          ← "xG timeline available in a few hours"
│   └── HistoryList.tsx           ← analysis history with team filter
├── lib/
│   └── api.ts                    ← typed fetch wrappers for all endpoints
└── package.json
```

### Key screens

**Home (`/`):** Pick a match. Shows a list of recent matches from the active mode. One click opens the analysis view.

**Analysis (`/analysis/[id]`):**
- Visualization picker (only shows charts available for the active mode)
- Generated chart with download button
- "View Visualization" expander persists while reading drafts
- Generate Content button → Newsletter / Twitter Thread tabs
- Context label: "Based on: Match Stats — France | France 2–1 Morocco | WC 2026 QF"

**History (`/history`):**
- List of saved analyses, newest first
- Filter by team (text input → filters `tags` array)
- Click any row → opens the analysis view with saved chart and last draft

---

## Tech Stack

| Layer | Technology | Hosting |
|-------|-----------|---------|
| Frontend | Next.js 14, TypeScript, Tailwind CSS | Vercel |
| Backend | FastAPI, Python 3.11 | Railway |
| Database | Supabase (PostgreSQL) | Supabase |
| Visualizations | mplsoccer, Matplotlib, Plotly | Backend |
| AI content | Claude API (claude-sonnet-4-6) | Backend |
| WC data | API-Football + soccerdata (FBref) | Backend |
| Historical data | StatsBomb Open Data | Backend |

---

## Build Milestones

Execute in order. Each milestone is a usable stopping point — if the World Cup deadline arrives, whatever is deployed is the tool.

### Milestone A — FastAPI backend (local)
- Data provider abstraction + both providers working
- All visualization endpoints returning base64 PNGs
- Content generation endpoint
- No Supabase yet — no persistence

### Milestone B — Next.js frontend (local, connected to backend)
- Home screen with match selection
- Analysis view: charts, content tabs, visualization expander
- No history page yet

### Milestone C — Supabase integration
- `analyses` and `drafts` tables created
- Backend saves on every generate + content call
- History page with team filter

### Milestone D — Deployment
- Backend → Railway
- Frontend → Vercel
- All env vars configured in both platforms
- Full end-to-end test on production URLs

---

## Environment Variables

### Backend (`.env`)

```
APP_MODE=statsbomb              # or world_cup
ANTHROPIC_API_KEY=...
API_FOOTBALL_KEY=...
SUPABASE_URL=...
SUPABASE_SERVICE_KEY=...
```

### Frontend (`.env.local`)

```
NEXT_PUBLIC_API_URL=http://localhost:8000   # Railway URL in production
```

---

## What's deferred (not in Stage 4)

- Auth / login
- Sharing or public access
- Beehiiv direct posting
- Twitter direct posting
- Saudi Pro League (needs API-Football upgrade)
- Set piece analysis, tactical shape (tracking data required)

---

## Timeline

World Cup starts June 11, 2026 — 4 weeks from spec approval.

Target: Milestones A + B complete by June 4. Milestones C + D by June 10.

The Streamlit app (`src/app.py`) remains untouched as a local fallback throughout.
