import os
from dotenv import load_dotenv

load_dotenv()

MAPBOX_TOKEN = os.getenv("MAPBOX_ACCESS_TOKEN")

if not MAPBOX_TOKEN:
    raise ValueError("MAPBOX_ACCESS_TOKEN not found in environment")