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
