import json
import os
from typing import List, Tuple

from pydantic import BaseModel

from backend.config import MOCK_DATA_DIR, MOCK_MODE, PROD_DATA_DIR
from backend.models.driver import Driver
from backend.models.task import Task


class DriverPayload(BaseModel):
    id: int
    start_location: Tuple[float, float]
    vehicle_type: str
    capacity: float = 0.0
    available: bool = True


class TaskPayload(BaseModel):
    id: int
    pickup_location: Tuple[float, float]
    dropoff_location: Tuple[float, float]
    weight: float = 0.0
    status: str = "unassigned"


def _active_data_dir() -> str:
    return MOCK_DATA_DIR if MOCK_MODE else PROD_DATA_DIR


def load_route_seed_data() -> Tuple[List[Driver], List[Task]]:
    data_dir = _active_data_dir()
    drivers_path = os.path.join(data_dir, "drivers.json")
    tasks_path = os.path.join(data_dir, "tasks.json")

    with open(drivers_path, "r", encoding="utf-8") as f:
        raw_drivers = json.load(f)
    with open(tasks_path, "r", encoding="utf-8") as f:
        raw_tasks = json.load(f)

    if not isinstance(raw_drivers, list) or not isinstance(raw_tasks, list):
        raise ValueError("drivers.json and tasks.json must each contain a JSON array.")

    drivers: List[Driver] = []
    for item in raw_drivers:
        payload = DriverPayload.model_validate(item)
        drivers.append(
            Driver(
                id=payload.id,
                start_location=payload.start_location,
                vehicle_type=payload.vehicle_type,
                capacity=payload.capacity,
                available=payload.available,
            )
        )

    tasks: List[Task] = []
    for item in raw_tasks:
        payload = TaskPayload.model_validate(item)
        tasks.append(
            Task(
                id=payload.id,
                pickup_location=payload.pickup_location,
                dropoff_location=payload.dropoff_location,
                weight=payload.weight,
                status=payload.status,
            )
        )

    return drivers, tasks
