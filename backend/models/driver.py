from dataclasses import dataclass
from typing import Tuple

@dataclass
class Driver:
    id: int
    start_location: Tuple[float, float]  #(x, y)
    vehicle_type: str                    # 'fuel' or 'ev'
    capacity: float = 0.0                # in kg, default 0.0
    available: bool = True

    @staticmethod
    def from_json(d: dict) -> "Driver":
        return Driver(
            id=d["id"],
            start_location=tuple(d["start_location"]),
            vehicle_type=d["vehicle_type"],
            capacity=float(d.get("capacity", 0.0)),
            available=d.get("available", True)
        )