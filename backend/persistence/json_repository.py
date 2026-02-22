import os
import json
from typing import List, Dict, Any
from .base import BaseRepository


class JSONRepository(BaseRepository):

    def __init__(self, base_path: str = "backend/data"):
        self.base_path = base_path
        os.makedirs(self.base_path, exist_ok=True)

        self.drivers_file = os.path.join(self.base_path, "persist_drivers.json")
        self.tasks_file = os.path.join(self.base_path, "persist_tasks.json")
        self.routes_file = os.path.join(self.base_path, "persist_routes.json")

    def _read(self, file_path: str):
        if not os.path.exists(file_path):
            return []
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _write(self, file_path: str, data):
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def save_driver(self, driver: Dict[str, Any]) -> None:
        data = self._read(self.drivers_file)
        data.append(driver)
        self._write(self.drivers_file, data)

    def save_task(self, task: Dict[str, Any]) -> None:
        data = self._read(self.tasks_file)
        data.append(task)
        self._write(self.tasks_file, data)

    def save_route_result(self, route_data: Dict[str, Any]) -> None:
        data = self._read(self.routes_file)
        data.append(route_data)
        self._write(self.routes_file, data)

    def load_drivers(self) -> List[Dict[str, Any]]:
        return self._read(self.drivers_file)

    def load_tasks(self) -> List[Dict[str, Any]]:
        return self._read(self.tasks_file)

    def load_routes(self) -> List[Dict[str, Any]]:
        return self._read(self.routes_file)