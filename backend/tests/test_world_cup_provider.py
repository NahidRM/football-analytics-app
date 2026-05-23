import pytest
from unittest.mock import patch, MagicMock
from backend.providers.world_cup import WorldCupProvider, _YOUTH
from backend.providers.base import Match, MatchStats, Lineup


FAKE_WC_LEAGUE = {"id": 1, "season": 2026, "name": "FIFA World Cup 2026", "is_warmup": False}
FAKE_FRIENDLY_LEAGUE = {"id": 10, "season": 2026, "name": "International Friendlies", "is_warmup": True}

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
    matches = provider._parse_fixtures(FAKE_FIXTURES_RESPONSE["response"], FAKE_WC_LEAGUE)
    assert len(matches) == 1
    m = matches[0]
    assert m.match_id == "apf:12345"
    assert m.home_team == "France"
    assert m.away_team == "Morocco"
    assert m.home_score == 2
    assert m.away_score == 1
    assert m.is_warmup is False
    assert m.competition == "FIFA World Cup 2026"


def test_parse_warmup_matches():
    provider = WorldCupProvider.__new__(WorldCupProvider)
    matches = provider._parse_fixtures(FAKE_FIXTURES_RESPONSE["response"], FAKE_FRIENDLY_LEAGUE)
    assert len(matches) == 1
    m = matches[0]
    assert m.is_warmup is True
    assert m.competition == "International Friendlies"
    assert m.is_live is True


def test_youth_filter_regex():
    # These should be blocked
    assert _YOUTH.search("Hungary U17")
    assert _YOUTH.search("Tajikistan U20")
    assert _YOUTH.search("England U21")
    assert _YOUTH.search("Brazil U23")
    # These should NOT be blocked
    assert not _YOUTH.search("Uruguay")
    assert not _YOUTH.search("France")
    assert not _YOUTH.search("Mexico")


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
    import sys
    original = sys.modules.pop("soccerdata", None)
    sys.modules["soccerdata"] = None  # type: ignore
    try:
        result = provider.get_shot_data("apf:12345")
        assert result is None
    finally:
        if original is not None:
            sys.modules["soccerdata"] = original
        else:
            sys.modules.pop("soccerdata", None)


def test_parse_fbref_shots_returns_none_on_none_input():
    provider = WorldCupProvider.__new__(WorldCupProvider)
    result = provider._parse_fbref_shots(None, None)
    assert result is None
