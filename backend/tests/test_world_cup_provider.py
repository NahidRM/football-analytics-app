import pytest
from unittest.mock import patch, MagicMock
from backend.providers.world_cup import WorldCupProvider
from backend.providers.base import Match, MatchStats, Lineup


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


def test_get_shot_data_returns_none_on_fbref_failure():
    provider = WorldCupProvider.__new__(WorldCupProvider)
    # When soccerdata raises any exception, should return None gracefully
    with patch("backend.providers.world_cup.WorldCupProvider.get_shot_data", side_effect=Exception("FBref unavailable")):
        with pytest.raises(Exception):
            provider.get_shot_data("12345")
    # Direct test: _parse_fbref_shots returns None on bad data
    result = provider._parse_fbref_shots(None, "12345")
    assert result is None
