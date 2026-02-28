from typing import Literal

from backend.config import MAPBOX_TOKEN, OPTIMIZER_MAP_MODE, OPTIMIZER_MAPBOX_FALLBACK

RoadMode = Literal["mapbox", "euclidean"]


def choose_preferred_mode() -> RoadMode:
    if OPTIMIZER_MAP_MODE == "euclidean":
        return "euclidean"
    if OPTIMIZER_MAP_MODE == "mapbox":
        return "mapbox"
    if MAPBOX_TOKEN:
        return "mapbox"
    return "euclidean"


def can_fallback_to_euclidean(preferred_mode: RoadMode) -> bool:
    return preferred_mode == "mapbox" and OPTIMIZER_MAPBOX_FALLBACK
