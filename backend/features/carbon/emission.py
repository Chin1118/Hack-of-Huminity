from typing import Tuple

# Constants
FUEL_EMISSION_FACTOR = 2.31  # kg CO2 per liter (Gasoline)
EV_GRID_EMISSION_FACTOR = 0.5  # kg CO2 per kWh (Grid average)

# Fuel Vehicle Parameters (Example: Light Van)
FUEL_CONSUMPTION_BASE = 0.10  # Liters per km (10L/100km)

# EV Parameters (Example: Electric Van)
EV_ENERGY_CONSUMPTION = 0.20  # kWh per km

def calculate_carbon_emission(
    vehicle_type: str,
    distance_km: float,
    time_hours: float,
    payload_weight: float = 0.0,
) -> float:
    """
    Calculate estimated CO2 emissions for a trip segment.
    
    Args:
        vehicle_type: 'fuel' or 'ev'
        distance_km: Distance traveled in km
        time_hours: Duration of the segment in hours
        payload_weight: Cargo weight in kg (affects consumption)
        
    Returns:
        float: Estimated CO2 emission in kg
    """
    vehicle_type = vehicle_type.lower()
    
    # Payload factor: roughly 1% extra fuel/energy per 50kg
    load_factor = 1.0 + (payload_weight / 5000.0)  # Simplified linear increase

    if vehicle_type == 'fuel':
        fuel_needed = (distance_km * FUEL_CONSUMPTION_BASE * load_factor) 
        carbon_emission = fuel_needed * FUEL_EMISSION_FACTOR
        return carbon_emission
    elif vehicle_type == 'ev':
        energy_needed = (distance_km * EV_ENERGY_CONSUMPTION * load_factor)
        carbon_emission = energy_needed * EV_GRID_EMISSION_FACTOR
        return carbon_emission
    else:
        # Default fallback or error
        return 0.0
