# Analysis types available per provider, keyed by match_id prefix.
# The prefix tells us which provider (and therefore which data model) owns the match.
_ANALYSES_BY_PREFIX = {
    "sb:":  ["passing_network", "heat_map", "shot_map", "press_map"],
    "apf:": ["match_stats", "player_ratings"],  # xg_timeline added only when FBref data exists
}


def get_available_analyses(match_id: str, fbref_available: bool = False) -> list[str]:
    """Return the analysis types available for a given match.

    fbref_available: pass True only when get_shot_data() returned real data —
    xg_timeline is only surfaced when there's actually something to plot.
    """
    for prefix, analyses in _ANALYSES_BY_PREFIX.items():
        if match_id.startswith(prefix):
            result = list(analyses)
            if prefix == "apf:" and fbref_available:
                result.append("xg_timeline")
            return result
    return []
