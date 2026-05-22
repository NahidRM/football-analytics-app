import pytest
from backend.providers.statsbomb import StatsBombProvider
from backend.providers.base import Match, MatchStats, Lineup


def test_get_matches_returns_list():
    provider = StatsBombProvider()
    matches = provider.get_matches()
    assert isinstance(matches, list)
    assert len(matches) > 0


def test_match_has_required_fields():
    provider = StatsBombProvider()
    matches = provider.get_matches()
    m = matches[0]
    assert isinstance(m.match_id, str)
    assert isinstance(m.label, str)
    assert isinstance(m.home_team, str)
    assert isinstance(m.home_score, int)


def test_match_ids_have_sb_prefix():
    provider = StatsBombProvider()
    matches = provider.get_matches()
    assert all(m.match_id.startswith("sb:") for m in matches)


def test_get_lineup_returns_lineup():
    # FA Women's Super League 2018/19, Reading WFC vs Everton LFC — a known StatsBomb free match
    provider = StatsBombProvider()
    lineup = provider.get_lineup("sb:2275127")
    assert isinstance(lineup, Lineup)
    assert len(lineup.home_players) > 0
    assert len(lineup.away_players) > 0


def test_get_shot_data_returns_list_or_none():
    provider = StatsBombProvider()
    shots = provider.get_shot_data("sb:2275127")
    # StatsBomb always has shot data
    assert shots is not None
    assert isinstance(shots, list)
