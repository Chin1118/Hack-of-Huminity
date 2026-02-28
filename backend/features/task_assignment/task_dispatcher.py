from __future__ import annotations

import math
from collections import defaultdict
from typing import Any, Dict, Iterable, List, Tuple


LngLat = Tuple[float, float]


class TaskDispatcher:
    """
    Build overlapping candidate task lists for nearby available drivers.
    """

    def __init__(self, drivers: Iterable[Any]):
        self.available_drivers = [d for d in drivers if getattr(d, "available", True)]

    @staticmethod
    def _to_lng_lat(value: Any) -> LngLat:
        if isinstance(value, (list, tuple)) and len(value) == 2:
            return float(value[0]), float(value[1])
        return (0.0, 0.0)

    @staticmethod
    def _distance(a: LngLat, b: LngLat) -> float:
        # Lightweight geodesic approximation for candidate filtering.
        return math.dist(a, b)

    def build_available_task_candidates(
        self,
        tasks: Iterable[Any],
        top_k: int = 3,
    ) -> Dict[str, List[str]]:
        """
        Returns mapping: driver_id -> [task_id, ...]
        Each task is assigned to K nearest available drivers (overlap allowed).
        """
        if not self.available_drivers:
            return {}

        normalized_k = max(1, min(int(top_k), len(self.available_drivers)))
        candidates: Dict[str, List[str]] = defaultdict(list)

        for task in tasks:
            pickup_location = self._to_lng_lat(getattr(task, "pickup_location", (0.0, 0.0)))
            ranked = sorted(
                self.available_drivers,
                key=lambda driver: self._distance(
                    self._to_lng_lat(getattr(driver, "start_location", (0.0, 0.0))),
                    pickup_location,
                ),
            )
            task_id = str(getattr(task, "id", ""))
            for driver in ranked[:normalized_k]:
                driver_id = str(getattr(driver, "id", ""))
                if not driver_id or not task_id:
                    continue
                candidates[driver_id].append(task_id)

        return dict(candidates)
