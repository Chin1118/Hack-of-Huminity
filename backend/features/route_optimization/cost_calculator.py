import numpy as np
from typing import Tuple

# Constants
FUEL_EMISSION_FACTOR = 2.31  # kg CO2 per liter (Gasoline)
EV_GRID_EMISSION_FACTOR = 0.5  # kg CO2 per kWh (Grid average)

# Fuel Vehicle Parameters (Example: Light Van)
FUEL_CONSUMPTION_BASE = 0.10  # Liters per km (10L/100km)

# EV Parameters (Example: Electric Van)
EV_ENERGY_CONSUMPTION = 0.20  # kWh per km

# Constants for Heuristic
EPSILON = 0.01

# Calculate Euclidean distance between two points
def calculate_distance(loc1: Tuple[float, float], loc2: Tuple[float, float]) -> float:
    return float(np.linalg.norm(np.array(loc1) - np.array(loc2)))

# Calculate CO2 emission based on distance and vehicle type
def calculate_carbon_emission(distance: float, vehicle_type: str, payload_weight: float = 0.0) -> float:
    vehicle_type = vehicle_type.lower()
    
    # Payload factor: roughly 1% extra fuel/energy per 50kg
    load_factor = 1.0 + (payload_weight / 5000.0)  # Simplified linear increase

    if vehicle_type == 'fuel':
        fuel_needed = (distance * FUEL_CONSUMPTION_BASE * load_factor) 
        carbon_emission = fuel_needed * FUEL_EMISSION_FACTOR
        return carbon_emission
    elif vehicle_type == 'ev':
        energy_needed = (distance * EV_ENERGY_CONSUMPTION * load_factor)
        carbon_emission = energy_needed * EV_GRID_EMISSION_FACTOR
        return carbon_emission
    else:
        # Default fallback or error
        return 0.0

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