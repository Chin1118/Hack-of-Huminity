from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class SolveRequest(BaseModel):
    driver_id: Optional[str] = None

class SolveResponse(BaseModel):
    driver_id: str
    best_path_nodes: List[str]
    metrics: Dict[str, float]
    mode_used: str


class DispatchAllRequest(BaseModel):
    top_k_candidates: int = 3


class DriverTaskAssignment(BaseModel):
    driver_id: str
    task_ids: List[str]


class DispatchAllResponse(BaseModel):
    mode_used: str
    assigned_count: int
    unassigned_count: int
    conflict_resolved_count: int
    driver_assignments: List[DriverTaskAssignment]


class RouteVisualizationItem(BaseModel):
    driver_id: str
    best_path_nodes: List[str]
    geometry: Dict[str, Any]
    distance_m: float
    duration_s: float
    color_hint: str
    driver_start_location: Optional[List[float]] = None
    pickup_points: List[List[float]] = []
    dropoff_points: List[List[float]] = []
    next_instruction: Optional[str] = None
    next_road_name: Optional[str] = None
    next_distance_m: Optional[float] = None
    next_maneuver_modifier: Optional[str] = None
    next_speed_limit_kmh: Optional[float] = None


class RouteVisualizationResponse(BaseModel):
    view_mode: str
    routes: List[RouteVisualizationItem]
