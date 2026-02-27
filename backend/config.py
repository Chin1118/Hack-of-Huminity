import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MOCK_MODE = os.getenv("MOCK_MODE", "false").strip().lower() in {"1", "true", "yes", "on"}
DATA_DIR = os.path.join(BASE_DIR, "data")
MOCK_DATA_DIR = os.path.join(DATA_DIR, "mock")
PROD_DATA_DIR = os.path.join(DATA_DIR, "production")

MAPBOX_TOKEN = os.getenv("MAPBOX_ACCESS_TOKEN")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not MAPBOX_TOKEN and not MOCK_MODE:
    raise ValueError("MAPBOX_ACCESS_TOKEN not found in environment")
