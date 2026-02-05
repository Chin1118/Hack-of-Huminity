from typing import Tuple

# Constants
FUEL_EMISSION_FACTOR = 2.31  # kg CO2 per liter (Gasoline)
EV_GRID_EMISSION_FACTOR = 0.5  # kg CO2 per kWh (Grid average)

# Fuel Vehicle Parameters (Example: Light Van)
FUEL_CONSUMPTION_BASE = 0.10  # Liters per km (10L/100km)
FUEL_IDLE_CONSUMPTION = 1.2   # Liters per hour

# EV Parameters (Example: Electric Van)
EV_ENERGY_CONSUMPTION = 0.20  # kWh per km
EV_IDLE_CONSUMPTION = 0.5     # kWh per hour (AC/Electronics)

def calculate_carbon_emission(
    vehicle_type: str,
    distance_km: float,
    time_hours: float,
    payload_weight: float = 0.0,
    is_stopping: bool = False
) -> float:
    """
    Calculate estimated CO2 emissions for a trip segment.
    
    Args:
        vehicle_type: 'fuel' or 'ev'
        distance_km: Distance traveled in km
        time_hours: Duration of the segment in hours
        payload_weight: Cargo weight in kg (affects consumption)
        is_stopping: If True, treats this segment as idling/stopping (distance should be ~0)
        
    Returns:
        float: Estimated CO2 emission in kg
    """
    vehicle_type = vehicle_type.lower()
    
    # Payload factor: roughly 1% extra fuel/energy per 50kg
    load_factor = 1.0 + (payload_weight / 5000.0)  # Simplified linear increase

    if vehicle_type == 'fuel':
        return _calculate_fuel_emission(distance_km, time_hours, load_factor, is_stopping)
    elif vehicle_type == 'ev':
        return _calculate_ev_emission(distance_km, time_hours, load_factor, is_stopping)
    else:
        # Default fallback or error
        return 0.0

def _calculate_fuel_emission(dist, time, load_factor, is_stopping) -> float:
    if is_stopping:
        fuel_needed = time * FUEL_IDLE_CONSUMPTION
    else:
        # Basic model: Distance-based consumption * load + small time penalty for traffic
        # We assume 'time' accounts for traffic if avg speed is low, but here we use a simpler model
        fuel_needed = (dist * FUEL_CONSUMPTION_BASE * load_factor) 
    
    return fuel_needed * FUEL_EMISSION_FACTOR

def _calculate_ev_emission(dist, time, load_factor, is_stopping) -> float:
    if is_stopping:
        energy_needed = time * EV_IDLE_CONSUMPTION
    else:
        energy_needed = (dist * EV_ENERGY_CONSUMPTION * load_factor)
        
    return energy_needed * EV_GRID_EMISSION_FACTOR
