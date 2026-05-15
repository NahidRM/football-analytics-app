ANALYSIS_REGISTRY = {
    "passing_network": ["statsbomb"],
    "heat_map":        ["statsbomb"],
    "shot_map":        ["statsbomb"],
    "press_map":       ["statsbomb"],
    "match_stats":     ["world_cup"],
    "player_ratings":  ["world_cup"],
    "xg_timeline":     ["world_cup"],
}


def get_available_analyses(mode: str) -> list[str]:
    return [k for k, modes in ANALYSIS_REGISTRY.items() if mode in modes]
