# Stage 4 — Real Web App Migration Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:writing-plans to flesh out the specific task in this plan before implementing. This document is an architectural roadmap, not a task-level plan — it must be expanded into full implementation detail before building begins.

**Goal:** Migrate from Streamlit to a proper web app — Next.js frontend hosted on Vercel, FastAPI backend on Railway, Supabase for saving analysis history. Nahid can access it from any browser, analyses are saved, and content drafts are stored for editing later.

**Architecture:** FastAPI exposes REST endpoints that run the Python visualization pipeline. Next.js calls those endpoints and renders the charts as images. Supabase stores analysis records and draft content. Auth is out of scope for Stage 4 — single-user, no login.

**Prerequisite:** Stage 3 complete and working locally.

**Tech Stack:** FastAPI, Next.js 14 (App Router), TypeScript, Supabase (PostgreSQL), Vercel, Railway, python-dotenv

---

## Why migrate from Streamlit?

Streamlit is great for prototyping but has real limits: it re-runs the entire script on every interaction (slow), can't be properly shared with others, has no URL routing, and can't store data. FastAPI + Next.js is the industry standard for this kind of tool and teaches transferable skills.

---

## New Project Structure

```
Analysis app/
├── backend/                     ← FastAPI application
│   ├── main.py                  ← FastAPI app + all route definitions
│   ├── visualizations/          ← moved from src/visualizations/
│   │   ├── passing_network.py
│   │   ├── heat_map.py
│   │   ├── shot_map.py
│   │   └── press_map.py
│   ├── data_loader.py           ← same logic, remove @st.cache_data
│   ├── content_generator.py     ← unchanged from Stage 3
│   ├── config.py                ← unchanged
│   ├── requirements.txt         ← backend dependencies
│   └── Procfile                 ← Railway deployment config
│
├── frontend/                    ← Next.js application
│   ├── app/
│   │   ├── page.tsx             ← home: match selection
│   │   ├── analysis/
│   │   │   └── [id]/page.tsx   ← individual analysis view
│   │   └── layout.tsx
│   ├── components/
│   │   ├── MatchSelector.tsx
│   │   ├── AnalysisCard.tsx
│   │   └── ContentEditor.tsx
│   ├── lib/
│   │   └── api.ts               ← typed wrappers around backend endpoints
│   └── package.json
│
├── src/                         ← Stage 1-3 scripts (kept for reference)
└── docs/
```

---

## Backend API Endpoints (FastAPI)

| Method | Path | What it does |
|--------|------|--------------|
| GET | `/competitions` | Returns list of all StatsBomb competitions |
| GET | `/matches/{competition_id}/{season_id}` | Returns matches for a comp+season |
| POST | `/analyze` | Runs a visualization; returns PNG as base64 + stats summary |
| POST | `/content` | Calls Claude API; returns newsletter + twitter drafts |
| GET | `/analyses` | Returns saved analysis history from Supabase |
| POST | `/analyses` | Saves an analysis record to Supabase |

The `/analyze` endpoint accepts: `{ match_id, team, analysis_type, player_name? }` and returns `{ image_base64, stats_summary, match_label }`.

---

## Database Schema (Supabase)

```sql
-- One row per saved analysis
CREATE TABLE analyses (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  created_at    TIMESTAMPTZ DEFAULT now(),
  match_id      INTEGER NOT NULL,
  match_label   TEXT NOT NULL,
  team          TEXT NOT NULL,
  analysis_type TEXT NOT NULL,
  player_name   TEXT,                -- nullable, only for heat maps
  image_url     TEXT,                -- Supabase Storage path (optional for now)
  newsletter    TEXT,                -- saved draft
  twitter       TEXT                 -- saved draft
);
```

---

## Key Implementation Milestones

When ready to build Stage 4, use `superpowers:writing-plans` to turn each milestone below into a full task-level plan. Do them in order — each builds on the last.

### Milestone A: FastAPI backend working locally
- `backend/main.py` with all endpoints
- Remove `@st.cache_data` from data_loader (replace with functools.lru_cache or no caching)
- All visualization draw_* functions callable from API endpoints
- Test with: `uvicorn backend.main:app --reload`, hit endpoints via browser or curl

### Milestone B: Next.js frontend working locally, connected to backend
- Match selector that calls `/competitions` and `/matches`
- Analysis form that calls `/analyze` and displays the returned image
- Content section that calls `/content`
- No Supabase yet — no saved history

### Milestone C: Supabase integration
- Create Supabase project at supabase.com (free tier)
- Add `analyses` table via SQL editor
- `POST /analyses` saves a record after generation
- `GET /analyses` fetches history
- Add analysis history page to frontend

### Milestone D: Deployment
- Backend → Railway: add `Procfile`, push to GitHub, connect to Railway
- Frontend → Vercel: connect GitHub repo, set `NEXT_PUBLIC_API_URL` env var
- Test full flow on production URLs
- Add environment variables: `ANTHROPIC_API_KEY`, `SUPABASE_URL`, `SUPABASE_ANON_KEY`

---

## Things to decide before building Stage 4

These were deferred intentionally — answer them when Stage 4 starts:

1. **Auth or no auth?** If Nahid wants to share the app with others later, add Supabase Auth (email OTP). If it's personal-only, skip auth entirely for Stage 4.
2. **Image storage?** Save PNGs to Supabase Storage (adds a few steps) or just regenerate on demand (simpler, slower).
3. **One repo or two?** Backend and frontend can live in the same git repo (monorepo) or separate repos. Monorepo is simpler for a solo project.

---

**Estimated timeline:** 4-6 weeks part-time, working through it with Claude Code.
**Next:** Stage 5 — see `docs/superpowers/plans/2026-05-12-stage-5-polish.md`
