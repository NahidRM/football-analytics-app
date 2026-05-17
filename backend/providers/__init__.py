from backend.config import APP_MODE
from backend.providers.base import DataProvider


def get_active_provider() -> DataProvider:
    if APP_MODE == "statsbomb":
        from backend.providers.statsbomb import StatsBombProvider
        return StatsBombProvider()
    if APP_MODE == "world_cup":
        from backend.providers.world_cup import WorldCupProvider
        return WorldCupProvider()
    raise NotImplementedError(f"No provider for APP_MODE='{APP_MODE}'")
