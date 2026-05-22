from backend.visualizations import get_available_analyses


def test_statsbomb_analyses():
    result = get_available_analyses("sb:123")
    assert set(result) == {"passing_network", "heat_map", "shot_map", "press_map"}


def test_world_cup_analyses():
    result = get_available_analyses("apf:456")
    assert set(result) == {"match_stats", "player_ratings", "xg_timeline"}


def test_unknown_prefix_returns_empty():
    result = get_available_analyses("unknown:789")
    assert result == []


def test_all_seven_analysis_types_covered():
    sb_types = set(get_available_analyses("sb:1"))
    apf_types = set(get_available_analyses("apf:1"))
    assert sb_types | apf_types == {
        "passing_network", "heat_map", "shot_map", "press_map",
        "match_stats", "player_ratings", "xg_timeline",
    }


def test_visualization_modules_are_importable():
    """Ensure the copied modules can be imported without error."""
    import backend.visualizations.passing_network
    import backend.visualizations.heat_map
    import backend.visualizations.shot_map
    import backend.visualizations.press_map
