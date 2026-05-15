from backend.config import APP_MODE
from backend.providers.base import DataProvider


def get_active_provider() -> DataProvider:
    if APP_MODE == "statsbomb":
        from backend.providers.statsbomb import StatsBombProvider
        return StatsBombProvider()
    from backend.providers.world_cup import WorldCupProvider
    return WorldCupProvider()
