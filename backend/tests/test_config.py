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
