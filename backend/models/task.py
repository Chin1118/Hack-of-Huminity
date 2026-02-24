from dataclasses import dataclass
from typing import Tuple

@dataclass
class Task:
    id: int
    pickup_location: Tuple[float, float]        #(lat, lon) 
    pickup_time_window: Tuple[float, float]     #(earliest_pickup, latest_pickup) in hours
    dropoff_location: Tuple[float, float]       #(lat, lon)
    dropoff_time_window: Tuple[float, float]    #(earliest_dropoff, latest_dropoff) in hours
    weight: float = 0.00                        #in kg, default 0.0
    status: str = "unassigned"                 # 'unassigned', 'assigned', 'picked_up', 'delivered'

# If do any change should change to also converters/task.py, and maybe api/schemas/task.py