import numpy as np
from typing import Tuple

# Constants for CO2 calculation (placeholder values)
CO2_FACTOR_FUEL = 0.2  # kg CO2 / km
CO2_FACTOR_EV = 0.05   # kg CO2 / km (grid emission equivalent)

# Constants for Heuristic
EPSILON = 0.01

# Calculate Euclidean distance between two points
def calculate_distance(loc1: Tuple[float, float], loc2: Tuple[float, float]) -> float:
    return float(np.linalg.norm(np.array(loc1) - np.array(loc2)))

# Calculate CO2 emission based on distance and vehicle type
def calculate_carbon_emission(distance: float, vehicle_type: str) -> float:
    if vehicle_type.lower() == 'ev':
        return distance * CO2_FACTOR_EV
    else:
        return distance * CO2_FACTOR_FUEL

# Calculate time based on distance and average speed (km/h)
def calculate_time(distance: float, speed: float = 50.0) -> float:
    if speed <= 0:
        return float('inf')
    return distance / speed

# Calculate heuristic value η = 1 / (CO₂_estimate + ε)
def calculate_heuristic(co2_estimate: float) -> float:
    return 1.0 / (co2_estimate + EPSILON)

# Calculate total cost = α * time + β * CO₂
def calculate_total_cost(alpha: float, beta: float, loc1: Tuple[float, float], loc2: Tuple[float, float], vehicle_type: str) -> float:
    distance = calculate_distance(loc1, loc2)
    time_cost = calculate_time(distance)
    co2_cost = calculate_carbon_emission(distance, vehicle_type)
    heuristic = calculate_heuristic(co2_cost)
    return alpha * time_cost + beta * heuristic
