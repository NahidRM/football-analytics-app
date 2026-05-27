from __future__ import annotations
import base64
import io
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import logging
import threading
from contextlib import asynccontextmanager

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Absolute path to the Next.js static export output directory.
# Path(__file__) is backend/main.py, so .parent.parent is the repo root.
_FRONTEND_OUT = Path(__file__).parent.parent / "frontend" / "out"

from backend.providers import get_provider_for_match, get_all_matches, get_cached_match
from backend.providers.base import DataProvider
from backend.content_generator import generate_content
from backend.visualizations import get_available_analyses


def _preload_matches() -> None:
    """Warm the match cache in a background thread so the first request is instant."""
    try:
        get_all_matches()
        logging.info("Match cache pre-warmed successfully.")
    except Exception as exc:
        logging.warning("Match cache pre-warm failed: %s", exc)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start cache preloading immediately when the server boots — non-blocking.
    thread = threading.Thread(target=_preload_matches, daemon=True)
    thread.start()
    yield


app = FastAPI(title="The Whiteboard API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # local dev only; production is same-origin
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request models ─────────────────────────────────────────────────────────────

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


# ── Routes ────────────────────────────────────────────────────────────────────

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


@app.get("/competitions")
def list_competitions():
    """Return distinct competitions for the match selector UI."""
    seen: dict[str, dict] = {}
    for m in get_all_matches():
        key = f"{m.competition}|{m.season}"
        if key not in seen:
            seen[key] = {
                "competition": m.competition,
                "season": m.season,
                "country": m.country,
                "is_live": m.is_live,
                "is_warmup": m.is_warmup,
                "match_count": 0,
            }
        seen[key]["match_count"] += 1
    return list(seen.values())


@app.get("/matches/{match_id}")
def get_match(match_id: str):
    try:
        provider = get_provider_for_match(match_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    # --- Lineup (fast: statsbombpy caches per-match on disk) ---
    # We get home/away team names from the lineup rather than iterating
    # all 75 competition-seasons — that's the expensive call we're avoiding.
    try:
        lineup = provider.get_lineup(match_id)
        home_players = lineup.home_players
        away_players = lineup.away_players
        lineup_home = lineup.home_team
        lineup_away = lineup.away_team
    except Exception:
        home_players = []
        away_players = []
        lineup_home = ""
        lineup_away = ""

    # --- Shot data (fast: statsbombpy caches per-match on disk) ---
    try:
        shot_data = provider.get_shot_data(match_id)
    except Exception:
        shot_data = None

    # --- Match metadata ---
    # Use the in-memory cache if it's already warm (populated by /matches or
    # the startup preload). If the cache is cold we fall back to the lineup
    # team names — the buttons still appear immediately.
    match = get_cached_match(match_id)

    # Cache miss for apf: matches — fall back to a live provider lookup.
    # StatsBomb has a disk cache; WorldCupProvider does not, so we fetch on demand.
    if match is None and match_id.startswith("apf:"):
        try:
            all_provider_matches = get_provider_for_match(match_id).get_matches()
            match = next((m for m in all_provider_matches if m.match_id == match_id), None)
        except Exception:
            pass

    return {
        "match_id": match_id,
        "label": match.label if match else match_id,
        "home_team": match.home_team if match else lineup_home,
        "away_team": match.away_team if match else lineup_away,
        "home_score": match.home_score if match else 0,
        "away_score": match.away_score if match else 0,
        "date": match.date if match else "",
        "competition": match.competition if match else "",
        "season": match.season if match else "",
        "country": match.country if match else "",
        "is_live": match.is_live if match else False,
        "is_warmup": match.is_warmup if match else False,
        "fbref_available": shot_data is not None,
        "available_analyses": get_available_analyses(match_id, fbref_available=shot_data is not None),
        "home_players": home_players,
        "away_players": away_players,
    }


@app.post("/analyze")
def analyze(req: AnalyzeRequest):
    try:
        provider = get_provider_for_match(req.match_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    shot_data = provider.get_shot_data(req.match_id)
    available = get_available_analyses(req.match_id, fbref_available=shot_data is not None)
    if req.analysis_type not in available:
        raise HTTPException(
            status_code=400,
            detail=f"'{req.analysis_type}' not available for match '{req.match_id}'. Available: {available}",
        )
    match = next((m for m in provider.get_matches() if m.match_id == req.match_id), None)
    match_label = match.label if match else req.match_id

    try:
        fig, stats_summary = _run_analysis(req, provider, shot_data, match_label)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    image_b64 = base64.b64encode(buf.read()).decode()

    return {
        "image_base64": image_b64,
        "stats_summary": stats_summary,
        "match_label": match_label,
        "fbref_available": shot_data is not None,
    }


@app.post("/content")
def content(req: ContentRequest):
    newsletter, twitter = generate_content(
        req.analysis_type, req.team, req.match_label, req.stats_summary
    )
    return {"newsletter": newsletter, "twitter": twitter}


# ── Analysis dispatch ─────────────────────────────────────────────────────────

def _run_analysis(req: AnalyzeRequest, provider: DataProvider, shot_data, match_label: str):
    t = req.analysis_type

    if t == "match_stats":
        from backend.visualizations.match_stats import draw_match_stats
        stats = provider.get_match_stats(req.match_id)
        fig = draw_match_stats(stats, match_label)
        summary = (
            f"{stats.home_team}: {stats.home.shots} shots "
            f"({stats.home.shots_on_target} on target), {stats.home.possession:.0f}% possession. "
            f"{stats.away_team}: {stats.away.shots} shots "
            f"({stats.away.shots_on_target} on target), {stats.away.possession:.0f}% possession."
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
    events = sb.events(match_id=int(req.match_id.removeprefix("sb:")))

    if t == "passing_network":
        from backend.visualizations.passing_network import draw_passing_network
        fig = draw_passing_network(events, req.team, match_label)
        passes = events[
            (events["type"] == "Pass") &
            (events["team"] == req.team) &
            (events["pass_outcome"].isna())
        ]
        return fig, f"Successful passes: {len(passes)}."

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


# ── Static frontend (production only) ────────────────────────────────────────
# Only registered when the Next.js build output exists.
# API routes above are registered first, so they always take priority.
if _FRONTEND_OUT.exists():
    app.mount("/_next", StaticFiles(directory=str(_FRONTEND_OUT / "_next")), name="next-assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        """Serve built frontend files; fall back to the correct page shell.

        Next.js static export generates one HTML file per *known* route.
        Dynamic routes (e.g. /analysis/[id]) only pre-render the IDs listed in
        generateStaticParams — not every possible match ID.  With the new static
        /analysis route, any /analysis or /analysis/* request should get the
        analysis page shell so the client-side JS can read the ?match= search
        param and fetch the right data.
        """
        file_path = _FRONTEND_OUT / full_path
        if file_path.is_file():
            return FileResponse(str(file_path))
        # Analysis routes: serve the analysis page shell (not the home page).
        # Handles /analysis (with or without ?match=... query params) and any
        # old /analysis/<id> deep-links that might be bookmarked.
        # Next.js exports the page as analysis.html (no trailing slash by default).
        if full_path == "analysis" or full_path.startswith("analysis/"):
            analysis_html = _FRONTEND_OUT / "analysis.html"
            if analysis_html.is_file():
                return FileResponse(str(analysis_html))
        return FileResponse(str(_FRONTEND_OUT / "index.html"))
