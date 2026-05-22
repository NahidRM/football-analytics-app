# Analysis types available per provider, keyed by match_id prefix.
# The prefix tells us which provider (and therefore which data model) owns the match.
_ANALYSES_BY_PREFIX = {
    "sb:":  ["passing_network", "heat_map", "shot_map", "press_map"],
    "apf:": ["match_stats", "player_ratings", "xg_timeline"],
}


def get_available_analyses(match_id: str) -> list[str]:
    """Return the analysis types available for a given match."""
    for prefix, analyses in _ANALYSES_BY_PREFIX.items():
        if match_id.startswith(prefix):
            return analyses
    return []
