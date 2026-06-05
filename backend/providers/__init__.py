import logging
import time

from backend.providers.base import DataProvider

logger = logging.getLogger(__name__)

_matches_cache: list | None = None
_matches_cache_time: float = 0.0
_CACHE_TTL = 3600  # 1 hour — keeps API Football calls to ~48/day (free tier is 100)


def _bust_cache():
    """Force the next get_all_matches() call to re-fetch from all providers."""
    global _matches_cache, _matches_cache_time
    _matches_cache = None
    _matches_cache_time = 0.0


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


def get_cached_match(match_id: str):
    """Return a match from cache without triggering a full load.

    Returns None if the cache is cold (not yet loaded) or the match
    isn't found. Safe to call at any time — never blocks.
    """
    if match_id.startswith("sb:"):
        from backend.providers.statsbomb import get_cached_matches
        cache = get_cached_matches()
        if cache is None:
            return None
        return next((m for m in cache if m.match_id == match_id), None)
    return None


def get_all_matches():
    """Fetch matches from all available providers, merged into one list.

    Results are cached for _CACHE_TTL seconds so repeated page loads don't
    burn through API Football's 100-requests/day free-tier quota.
    """
    global _matches_cache, _matches_cache_time
    if _matches_cache is not None and (time.time() - _matches_cache_time) < _CACHE_TTL:
        return _matches_cache

    from backend.providers.statsbomb import StatsBombProvider
    from backend.providers.world_cup import WorldCupProvider
    matches = []
    for Provider in (WorldCupProvider, StatsBombProvider):  # Live first
        try:
            matches.extend(Provider().get_matches())
        except Exception as e:
            logger.exception("Provider %s failed: %s", Provider.__name__, e)

    _matches_cache = matches
    _matches_cache_time = time.time()
    return matches
