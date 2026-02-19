from __future__ import annotations
import math
from typing import Tuple, Optional
import numpy as np
from backend.models.emission import EmissionModel

# Constants for Heuristic
EPSILON = 0.01

# Calculate Euclidean distance between two points
def calculate_distance(loc1: Tuple[float, float], loc2: Tuple[float, float]) -> float:
    a = np.array(loc1, dtype=float)
    b = np.array(loc2, dtype=float)
    if a.shape != (2,) or b.shape != (2,):
        raise ValueError("loc1 and loc2 must be (x, y)")
    return float(np.linalg.norm(a - b))

# Calculate CO2 emission based on distance and vehicle type
def calculate_carbon_emission(distance_km: float,vehicle_type: str,payload_weight_kg: float = 0.0,model: Optional[EmissionModel] = None,) -> float:

    m = model or EmissionModel()
    return m.calculate_emission(
        vehicle_type=vehicle_type,
        distance_km=distance_km,
        payload_weight_kg=payload_weight_kg,
    )

# Calculate time based on distance and average speed (km/h)
def calculate_time(distance: float, speed: float = 50.0) -> float:
    if distance < 0:
        raise ValueError("distance_km must be >= 0")
    if speed <= 0:
        return float("inf")
    return distance / speed

# Calculate heuristic value η = 1 / (CO₂_estimate + ε)
def calculate_heuristic(co2_estimate: float) -> float:
    if not math.isfinite(co2_estimate):
        return 0.0
    co2 = max(0.0, float(co2_estimate))
    return 1.0 / (co2 + EPSILON)

# Calculate total cost = α * time + β * CO₂
def calculate_total_cost(alpha: float, beta: float, time_cost: float, heuristic: float) -> float:
    return alpha * time_cost + beta * heuristic