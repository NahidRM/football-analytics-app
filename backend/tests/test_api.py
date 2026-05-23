import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from backend.providers.base import Match, MatchStats, TeamStats, Lineup, PlayerStat


def _mock_provider():
    m = MagicMock()
    m.get_matches.return_value = [
        Match(
            "apf:123", "France 2–1 Morocco | WC 2026 QF", "France", "Morocco", 2, 1, "2026-07-05",
            competition="FIFA World Cup 2026", season="2026", country="International", is_live=True,
        )
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
    m.get_lineup.return_value = Lineup(
        "France", "Morocco", "4-3-3", "4-2-3-1",
        ["Lloris", "Pavard", "Varane", "Upamecano", "Hernandez",
         "Tchouaméni", "Rabiot", "Griezmann", "Dembélé", "Giroud", "Mbappé"],
        ["Bounou", "Hakimi", "Aguerd", "Saiss", "Mazraoui",
         "Ounahi", "Amrabat", "Ziyech", "Boufal", "En-Nesyri", "Sabiri"],
    )
    return m


@pytest.fixture
def client():
    from backend.main import app
    return TestClient(app)


def test_get_matches(client):
    with patch("backend.main.get_all_matches", return_value=_mock_provider().get_matches()):
        response = client.get("/matches")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert data[0]["match_id"] == "apf:123"
    assert data[0]["label"] == "France 2–1 Morocco | WC 2026 QF"
    assert data[0]["is_live"] is True


def test_get_match_detail(client):
    with patch("backend.main.get_provider_for_match", return_value=_mock_provider()):
        response = client.get("/matches/apf:123")
    assert response.status_code == 200
    data = response.json()
    assert data["match_id"] == "apf:123"
    assert data["fbref_available"] is False
    assert set(data["available_analyses"]) == {"match_stats", "player_ratings"}  # xg_timeline only when fbref_available


def test_analyze_unknown_type_returns_400(client):
    with patch("backend.main.get_provider_for_match", return_value=_mock_provider()):
        response = client.post("/analyze", json={
            "match_id": "apf:123",
            "team": "France",
            "analysis_type": "unknown_type",
        })
    assert response.status_code == 400


def test_get_competitions(client):
    with patch("backend.main.get_all_matches", return_value=_mock_provider().get_matches()):
        response = client.get("/competitions")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    if data:
        for item in data:
            assert {"competition", "season", "country", "is_live", "match_count"} <= item.keys()


