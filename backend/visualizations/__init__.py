# Analysis types always available per provider prefix.
_ANALYSES_BY_PREFIX = {
    "sb:":  ["passing_network", "heat_map", "shot_map", "press_map"],
    "apf:": ["match_stats", "player_ratings", "pitch_card", "match_timeline"],
}

# Additional analyses unlocked only when FBref shot data is available.
_FBREF_ANALYSES = ["xg_timeline", "xg_xa_chart", "xg_vs_goals", "ebb_and_flow", "sub_impact"]


def get_available_analyses(match_id: str, fbref_available: bool = False) -> list[str]:
    """Return the analysis types available for a given match."""
    for prefix, analyses in _ANALYSES_BY_PREFIX.items():
        if match_id.startswith(prefix):
            result = list(analyses)
            if prefix == "apf:" and fbref_available:
                result.extend(_FBREF_ANALYSES)
            return result
    return []
