from backend.providers.base import DataProvider


def get_provider_for_match(match_id: str) -> DataProvider:
    """Route a namespaced match ID to the correct provider.

    StatsBomb IDs are prefixed with 'sb:' (e.g. 'sb:3749448').
    API-Football IDs are prefixed with 'apf:' (e.g. 'apf:1189662').
    """
    if match_id.startswith("sb:"):
        from backend.providers.statsbomb import StatsBombProvider
        return StatsBombProvider()
    if match_id.startswith("apf:"):
        from backend.providers.world_cup import WorldCupProvider
        return WorldCupProvider()
    raise ValueError(f"Unrecognised match_id prefix: '{match_id}'")


def get_all_matches():
    """Fetch matches from all available providers, merged into one list."""
    from backend.providers.statsbomb import StatsBombProvider
    from backend.providers.world_cup import WorldCupProvider
    matches = []
    for Provider in (WorldCupProvider, StatsBombProvider):  # Live first
        try:
            matches.extend(Provider().get_matches())
        except Exception:
            pass
    return matches
