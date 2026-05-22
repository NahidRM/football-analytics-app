from __future__ import annotations
import base64
import io
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.providers import get_provider_for_match, get_all_matches
from backend.providers.base import DataProvider
from backend.content_generator import generate_content
from backend.visualizations import get_available_analyses

app = FastAPI(title="The Whiteboard API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_origin_regex=r"https://.*\.vercel\.app",
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
    analysis_id: str | None = None


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
    match = next((m for m in provider.get_matches() if m.match_id == match_id), None)
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
        "available_analyses": get_available_analyses(match_id),
    }


@app.post("/analyze")
def analyze(req: AnalyzeRequest):
    available = get_available_analyses(req.match_id)
    if req.analysis_type not in available:
        raise HTTPException(
            status_code=400,
            detail=f"'{req.analysis_type}' not available for match '{req.match_id}'. Available: {available}",
        )

    try:
        provider = get_provider_for_match(req.match_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    shot_data = provider.get_shot_data(req.match_id)
    match = next((m for m in provider.get_matches() if m.match_id == req.match_id), None)
    match_label = match.label if match else req.match_id

    fig, stats_summary = _run_analysis(req, provider, shot_data, match_label)

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    image_b64 = base64.b64encode(buf.read()).decode()

    # Persist to Supabase (non-blocking — failure doesn't break the response)
    analysis_db_id = None
    try:
        from backend.db import save_analysis as db_save
        opponent = ""
        if match:
            opponent = match.away_team if match.home_team == req.team else match.home_team
        saved = db_save({
            "mode": "sb" if req.match_id.startswith("sb:") else "apf",
            "match_label": match_label,
            "team": req.team,
            "opponent": opponent,
            "analysis_type": req.analysis_type,
            "image_base64": image_b64,
            "stats_summary": stats_summary,
        })
        analysis_db_id = saved.get("id")
    except Exception:
        pass

    return {
        "image_base64": image_b64,
        "stats_summary": stats_summary,
        "match_label": match_label,
        "fbref_available": shot_data is not None,
        "analysis_id": analysis_db_id,
    }


@app.post("/content")
def content(req: ContentRequest):
    newsletter, twitter = generate_content(
        req.analysis_type, req.team, req.match_label, req.stats_summary
    )
    try:
        if req.analysis_id:
            from backend.db import save_draft
            save_draft(req.analysis_id, newsletter, twitter)
    except Exception:
        pass
    return {"newsletter": newsletter, "twitter": twitter}


@app.get("/analyses")
def list_analyses():
    try:
        from backend.db import get_analyses
        return get_analyses()
    except Exception:
        return []


@app.post("/analyses")
def save_analysis_endpoint(body: dict):
    try:
        from backend.db import save_analysis
        return save_analysis(body)
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
