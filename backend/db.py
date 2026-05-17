from __future__ import annotations
from supabase import create_client, Client
from backend.config import SUPABASE_URL, SUPABASE_SERVICE_KEY

try:
    _client: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
except Exception:
    _client = None  # type: ignore[assignment]


def save_analysis(record: dict) -> dict:
    if _client is None:
        raise RuntimeError("Supabase client is not configured — set SUPABASE_URL and SUPABASE_SERVICE_KEY")
    tags = list({v for v in (record.get("team"), record.get("opponent")) if v})
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
    if _client is None:
        raise RuntimeError("Supabase client is not configured — set SUPABASE_URL and SUPABASE_SERVICE_KEY")
    result = _client.table("drafts").insert({
        "analysis_id": analysis_id,
        "newsletter":  newsletter,
        "twitter":     twitter,
        "regenerated": regenerated,
    }).execute()
    return result.data[0]


def get_analyses(tag: str | None = None) -> list[dict]:
    if _client is None:
        raise RuntimeError("Supabase client is not configured — set SUPABASE_URL and SUPABASE_SERVICE_KEY")
    # tag filtering is done in Python — all rows are fetched first
    query = _client.table("analyses").select("*").order("created_at", desc=True)
    result = query.execute()
    rows = result.data or []
    if tag:
        rows = [r for r in rows if tag in (r.get("tags") or [])]
    return rows


def get_drafts(analysis_id: str) -> list[dict]:
    if _client is None:
        raise RuntimeError("Supabase client is not configured — set SUPABASE_URL and SUPABASE_SERVICE_KEY")
    result = (
        _client.table("drafts")
        .select("*")
        .eq("analysis_id", analysis_id)
        .order("created_at", desc=True)
        .execute()
    )
    return result.data or []
