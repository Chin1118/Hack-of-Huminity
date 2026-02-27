import json
import os
from typing import Any, Dict, List

from backend.config import MOCK_DATA_DIR, MOCK_MODE, PROD_DATA_DIR


MOCK_FALLBACK_DATA: Dict[str, Any] = {
    "drivers": [
        {
            "id": 9001,
            "start_location": [103.8198, 1.3521],
            "vehicle_type": "ev",
            "capacity": 250.0,
            "available": True,
        }
    ],
    "tasks": [
        {
            "id": 9001,
            "pickup_location": [103.8111, 1.3402],
            "dropoff_location": [103.8600, 1.3000],
            "weight": 10.0,
            "status": "unassigned",
        }
    ],
}


class JsonDataProvider:
    """
    Centralized JSON repository with a mock-mode switch.
    """

    def __init__(self, mock_mode: bool = MOCK_MODE):
        self.mock_mode = mock_mode

    def _base_dir(self) -> str:
        if self.mock_mode:
            return MOCK_DATA_DIR

        if not os.path.isdir(PROD_DATA_DIR):
            raise FileNotFoundError(
                f"Production JSON folder not found: {PROD_DATA_DIR}. "
                "Create it or enable MOCK_MODE=true."
            )
        return PROD_DATA_DIR

    def _file_path(self, dataset: str) -> str:
        return os.path.join(self._base_dir(), f"{dataset}.json")

    def load_list(self, dataset: str) -> List[Dict[str, Any]]:
        path = self._file_path(dataset)
        if not os.path.exists(path):
            if self.mock_mode:
                fallback = MOCK_FALLBACK_DATA.get(dataset, [])
                return list(fallback)
            return []

        with open(path, "r", encoding="utf-8") as f:
            raw = json.load(f)

        if not isinstance(raw, list):
            raise ValueError(f"{dataset}.json must contain a JSON list.")
        return raw

    def save_list(self, dataset: str, data: List[Dict[str, Any]]) -> None:
        path = self._file_path(dataset)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def load_dict(self, dataset: str) -> Dict[str, Any]:
        path = self._file_path(dataset)
        if not os.path.exists(path):
            if self.mock_mode:
                fallback = MOCK_FALLBACK_DATA.get(dataset, {})
                if isinstance(fallback, dict):
                    return dict(fallback)
                return {}
            return {}

        with open(path, "r", encoding="utf-8") as f:
            raw = json.load(f)

        if not isinstance(raw, dict):
            raise ValueError(f"{dataset}.json must contain a JSON object.")
        return raw

    def save_dict(self, dataset: str, data: Dict[str, Any]) -> None:
        path = self._file_path(dataset)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)


def get_data_provider() -> JsonDataProvider:
    return JsonDataProvider()
