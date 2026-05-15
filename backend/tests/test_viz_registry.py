from backend.visualizations import get_available_analyses, ANALYSIS_REGISTRY


def test_statsbomb_analyses():
    result = get_available_analyses("statsbomb")
    assert set(result) == {"passing_network", "heat_map", "shot_map", "press_map"}


def test_world_cup_analyses():
    result = get_available_analyses("world_cup")
    assert set(result) == {"match_stats", "player_ratings", "xg_timeline"}


def test_all_seven_analysis_types_registered():
    all_types = set(ANALYSIS_REGISTRY.keys())
    assert all_types == {
        "passing_network", "heat_map", "shot_map", "press_map",
        "match_stats", "player_ratings", "xg_timeline",
    }


def test_visualization_modules_are_importable():
    """Ensure the copied modules can be imported without error."""
    import backend.visualizations.passing_network
    import backend.visualizations.heat_map
    import backend.visualizations.shot_map
    import backend.visualizations.press_map
