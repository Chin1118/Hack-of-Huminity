import json
import os
from typing import List, Optional
from backend.models.driver import Driver

# JSON file path
DRIVERS_JSON_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "data",
    "drivers.json"
)

# Convert JSON dict to Driver object
def json_to_driver(data: dict) -> Driver:
    return Driver(
        id=data["id"],
        start_location=tuple(data["start_location"]),
        vehicle_type=data["vehicle_type"],
        capacity=float(data.get("capacity", 0.0)),
        available=data.get("available", True)
    )


# Convert Driver object to JSON dict
def driver_to_json(driver: Driver) -> dict:
    return {
        "id": driver.id,
        "start_location": list(driver.start_location),
        "vehicle_type": driver.vehicle_type,
        "capacity": driver.capacity,
        "available": driver.available
    }


# Load all drivers from JSON file
def load_drivers() -> List[Driver]:
    if not os.path.exists(DRIVERS_JSON_PATH): # Check if the JSON file exists
        return []
    
    try:
        with open(DRIVERS_JSON_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            return [json_to_driver(item) for item in data]
    except (json.JSONDecodeError, KeyError) as e:
        raise ValueError(f"JSON file format error: {e}")


# Save drivers to JSON file
def save_drivers(drivers: List[Driver]) -> None:
    os.makedirs(os.path.dirname(DRIVERS_JSON_PATH), exist_ok=True) # Create the directory if it doesn't exist
    
    data = [driver_to_json(driver) for driver in drivers]
    
    with open(DRIVERS_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# Find a single driver by ID
def find_driver_by_id(driver_id: int) -> Optional[Driver]: # May use in validation
    drivers = load_drivers()
    for driver in drivers:
        if driver.id == driver_id:
            return driver
    return None


# Add a new driver
def add_driver(driver: Driver) -> Driver:
    drivers = load_drivers()
    
    # Auto-generate ID (find max ID + 1)
    if drivers:
        max_id = max(d.id for d in drivers)
        driver.id = max_id + 1
    else:
        driver.id = 1
    
    drivers.append(driver)
    save_drivers(drivers)
    return driver


# Update a driver
def update_driver(driver_id: int, updated_driver: Driver) -> Optional[Driver]:
    drivers = load_drivers()
    
    for i, driver in enumerate(drivers):
        if driver.id == driver_id:
            # Keep ID unchanged
            updated_driver.id = driver_id
            drivers[i] = updated_driver
            save_drivers(drivers)
            return updated_driver
    
    return None


# Delete a driver
def delete_driver(driver_id: int) -> bool:
    drivers = load_drivers()
    
    for i, driver in enumerate(drivers):
        if driver.id == driver_id:
            drivers.pop(i)
            save_drivers(drivers)
            return True
    
    return False
