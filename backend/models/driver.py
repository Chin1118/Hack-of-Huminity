from dataclasses import dataclass
from typing import Tuple

@dataclass
class Driver:
    id: int
    start_location: Tuple[float, float]  #(x, y)
    vehicle_type: str                    # 'fuel' or 'ev'
    capacity: float = 0.0                # in kg, default 0.0
    available: bool = True

