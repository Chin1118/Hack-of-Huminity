import math
from typing import Tuple, Optional
import numpy as np
from backend.models.emission import EmissionModel
from backend.utils.road_network import RoadNetwork;

# Constants for Heuristic
EPSILON = 0.01

def calculate_distance(road_network: RoadNetwork, node_a_id: str, node_b_id: str) -> float:
    return road_network.get_distance_between_nodes(node_a_id, node_b_id)

def calculate_time(road_network: RoadNetwork, node_a_id: str, node_b_id: str) -> float:
    return road_network.get_travel_time_between_nodes(node_a_id, node_b_id)

# Calculate CO2 emission based on distance and vehicle type
def calculate_carbon_emission(model: EmissionModel, distance_km: float, vehicle_type: str, payload_weight_kg: float = 0.0) -> float:
    return model.calculate_emission(
        vehicle_type=vehicle_type,
        distance_km=distance_km,
        payload_weight_kg=payload_weight_kg,
    )

# Calculate heuristic value η = 1 / (CO₂_estimate + ε)
def calculate_heuristic(co2_estimate: float) -> float:
    if not math.isfinite(co2_estimate):
        return 0.0
    co2 = max(0.0, float(co2_estimate))
    return 1.0 / (co2 + EPSILON)

# Calculate total cost = α * time + β * CO₂
def calculate_total_cost(alpha: float, beta: float, time_cost: float, heuristic: float) -> float:
    return alpha * time_cost + beta * heuristic