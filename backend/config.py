import os
from dotenv import load_dotenv

load_dotenv()

APP_MODE = os.getenv("APP_MODE", "statsbomb")

if APP_MODE not in ("statsbomb", "world_cup"):
    raise ValueError(f"APP_MODE must be 'statsbomb' or 'world_cup', got '{APP_MODE}'")

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
API_FOOTBALL_KEY = os.getenv("API_FOOTBALL_KEY", "")
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "")
