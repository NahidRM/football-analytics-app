import pytest
from backend.visualizations import get_available_analyses


def test_app_mode_statsbomb(monkeypatch):
    monkeypatch.setenv("APP_MODE", "statsbomb")
    import importlib
    import backend.config as cfg
    importlib.reload(cfg)
    assert cfg.APP_MODE == "statsbomb"


def test_app_mode_world_cup(monkeypatch):
    monkeypatch.setenv("APP_MODE", "world_cup")
    import importlib
    import backend.config as cfg
    importlib.reload(cfg)
    assert cfg.APP_MODE == "world_cup"


def test_invalid_app_mode_raises(monkeypatch):
    monkeypatch.setenv("APP_MODE", "invalid_mode")
    import importlib
    import backend.config as cfg
    with pytest.raises(ValueError, match="APP_MODE must be"):
        importlib.reload(cfg)


def test_statsbomb_analyses():
    result = get_available_analyses("sb:1")
    assert "passing_network" in result
    assert "match_stats" not in result

def test_world_cup_analyses():
    result = get_available_analyses("apf:1")
    assert "match_stats" in result
    assert "player_ratings" in result
    assert "xg_timeline" in result
    assert "passing_network" not in result


def test_match_is_warmup_defaults_false():
    from backend.providers.base import Match
    m = Match(
        match_id="sb:1", label="Test", home_team="A", away_team="B",
        home_score=0, away_score=0, date="2026-06-01",
    )
    assert m.is_warmup is False


def test_match_is_warmup_can_be_set():
    from backend.providers.base import Match
    m = Match(
        match_id="apf:1", label="Test", home_team="A", away_team="B",
        home_score=0, away_score=0, date="2026-06-01",
        is_warmup=True,
    )
    assert m.is_warmup is True
