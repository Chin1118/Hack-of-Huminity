from dataclasses import dataclass
from typing import Tuple

@dataclass
class Task:
    id: int
    pickup_location: Tuple[float, float]        #(x, y) 
    pickup_time_window: Tuple[float, float]     #(earliest_pickup, latest_pickup) in hours
    dropoff_location: Tuple[float, float]       #(x, y)
    dropoff_time_window: Tuple[float, float]    #(earliest_dropoff, latest_dropoff) in hours
    weight: float = 0.00                        #in kg, default 0.0

    @staticmethod
    def from_json(t: dict) -> "Task":
        return Task(
            id=t["id"],
            pickup_location=tuple(t["pickup"]["location"]),
            pickup_time_window=tuple(t["pickup"]["time_window"]),
            dropoff_location=tuple(t["dropoff"]["location"]),
            dropoff_time_window=tuple(t["dropoff"]["time_window"]),
            weight=t["weight"]
        )