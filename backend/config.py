import os
from pathlib import Path

from dotenv import load_dotenv

# Load both project-root .env and backend/.env so running from root works.
ROOT_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = Path(__file__).resolve().parent
load_dotenv(ROOT_DIR / ".env")
load_dotenv(BACKEND_DIR / ".env")

MAPBOX_TOKEN = os.getenv("MAPBOX_ACCESS_TOKEN")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
ROLE_FALLBACK_ENABLED = os.getenv("ROLE_FALLBACK_ENABLED", "true").lower() == "true"
OPTIMIZER_MAP_MODE = os.getenv("OPTIMIZER_MAP_MODE", "auto").lower()
OPTIMIZER_MAPBOX_FALLBACK = os.getenv("OPTIMIZER_MAPBOX_FALLBACK", "true").lower() == "true"
