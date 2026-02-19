from pydantic import BaseModel
from typing import List, Dict, Any

class SolveRequest(BaseModel):
    driver_id: int

class SolveResponse(BaseModel):
    driver_id: int
    best_path_nodes: List[str]
    metrics: Dict[str, float]
