from __future__ import annotations
import math
from typing import Tuple, List, Dict, Any, Optional, Literal
import requests
from backend.config import MAPBOX_TOKEN

LngLat = Tuple[float, float]  # (lng, lat)
MAX_COORDS_PER_REQ = 25

class MapboxMatrixClient:
    def __init__(self, token: str = MAPBOX_TOKEN, profile: str = "driving"):
        if not token:
            raise ValueError("MAPBOX token is empty")
        self.token = token
        self.profile = profile

    def _call_matrix(self, coords: List[LngLat]) -> Dict[str, Any]:
        if len(coords) < 2:
            raise ValueError("Matrix API needs at least 2 coordinates")
        if len(coords) > MAX_COORDS_PER_REQ:
            raise ValueError(f"Too many coordinates: {len(coords)} > {MAX_COORDS_PER_REQ}")

        coords_str = ";".join([f"{lng},{lat}" for lng, lat in coords])
        url = f"https://api.mapbox.com/directions-matrix/v1/mapbox/{self.profile}/{coords_str}"

        params = {
            "access_token": self.token,
            "annotations": "duration,distance",
        }

        r = requests.get(url, params=params, timeout=20)
        if r.status_code != 200:
            raise RuntimeError(f"Mapbox Matrix error {r.status_code}: {r.text}")

        return r.json()

    def get_matrix(self, coords: List[LngLat]) -> Dict[str, List[List[Optional[float]]]]:
        """
        Returns:
          durations: seconds (n x n)
          distances: meters  (n x n)
        """
        n = len(coords)
        if n < 2:
            raise ValueError("Need at least 2 coordinates")

        if n <= MAX_COORDS_PER_REQ:
            data = self._call_matrix(coords)
            return {
                "durations": data.get("durations"),
                "distances": data.get("distances"),
            }

        durations: List[List[Optional[float]]] = [[None] * n for _ in range(n)]
        distances: List[List[Optional[float]]] = [[None] * n for _ in range(n)]

        blocks = [list(range(i, min(i + MAX_COORDS_PER_REQ, n))) for i in range(0, n, MAX_COORDS_PER_REQ)]

        for rb in blocks:
            for cb in blocks:
                merged_idx: List[int] = []
                seen = set()
                for idx in rb + cb:
                    if idx not in seen:
                        seen.add(idx)
                        merged_idx.append(idx)

                merged_coords = [coords[i] for i in merged_idx]
                data = self._call_matrix(merged_coords)

                durs = data.get("durations")
                diss = data.get("distances")
                if durs is None or diss is None:
                    raise RuntimeError("Mapbox Matrix response missing durations/distances")

                local_of = {orig_i: local_i for local_i, orig_i in enumerate(merged_idx)}

                for i in rb:
                    li = local_of[i]
                    for j in cb:
                        lj = local_of[j]
                        durations[i][j] = durs[li][lj]
                        distances[i][j] = diss[li][lj]

        return {"durations": durations, "distances": distances}

    def get_directions(self, coords: List[LngLat], steps: bool = False) -> Dict[str, Any]:
        """
        Fetches the detailed route geometry and turn-by-turn data for a sequence of points.
        Note: Mapbox driving profile allows up to 25 coordinates per request.
        """
        if len(coords) < 2:
            raise ValueError("Directions API needs at least 2 coordinates")
        if len(coords) > MAX_COORDS_PER_REQ:
            raise ValueError(f"Directions API allows max {MAX_COORDS_PER_REQ} waypoints per request.")

        # Mapbox expects longitude,latitude separated by semicolons
        coords_str = ";".join([f"{lng},{lat}" for lng, lat in coords])
        url = f"https://api.mapbox.com/directions/v5/mapbox/{self.profile}/{coords_str}"

        params = {
            "access_token": self.token,
            "geometries": "geojson",  # 'geojson' is usually easiest for frontend mapping (or 'polyline6')
            "overview": "full",       # gets the high-resolution path
            "steps": "true" if steps else "false",
            # Request posted speed metadata when available on road segments.
            "annotations": "maxspeed",
        }

        r = requests.get(url, params=params, timeout=20)
        if r.status_code != 200:
            raise RuntimeError(f"Mapbox Directions error {r.status_code}: {r.text}")

        return r.json()


class RoadNetwork:
    """
    Unified road network for ACO:
      - mode='euclidean': math.dist + speed
      - mode='mapbox': Mapbox Matrix for real road distance/duration
    """

    def __init__(
        self,
        drivers: List[Any],
        tasks: List[Any],
        mode: Literal["euclidean", "mapbox"] = "mapbox",
        speed_kmh: float = 50.0,
        mapbox_profile: str = "driving",
        mapbox_token: str = MAPBOX_TOKEN,
        warm_up_matrix: bool = True,
    ):
        self.mode = mode
        self.speed_kmh = speed_kmh

        # node_id -> (lng,lat)
        self.locations: Dict[str, LngLat] = {}

        # ---- build nodes ----
        for driver in drivers:
            self.locations[f"D_{driver.id}"] = tuple(driver.start_location)

        for task in tasks:
            self.locations[f"T_{task.id}"] = tuple(task.pickup_location)       # pickup
            self.locations[f"T_{task.id}_D"] = tuple(task.dropoff_location)    # dropoff
        
        # fix order and index for matrix
        self._nodes: List[str] = list(self.locations.keys())
        self._node_index: Dict[str, int] = {nid: i for i, nid in enumerate(self._nodes)}

        # cache for mapbox
        self._durations_s: Optional[List[List[Optional[float]]]] = None
        self._distances_m: Optional[List[List[Optional[float]]]] = None

        self._matrix_client: Optional[MapboxMatrixClient] = None
        if self.mode == "mapbox":
            self._matrix_client = MapboxMatrixClient(token=mapbox_token, profile=mapbox_profile)
            if warm_up_matrix:
                self._warm_up_matrix()

    # ---------- basic ----------
    def get_all_nodes(self) -> List[str]:
        return list(self._nodes)

    def get_location(self, node_id: str) -> LngLat:
        return self.locations.get(node_id, (0.0, 0.0))

    # ---------- euclidean ----------
    def _euclidean_distance_km(self, a: LngLat, b: LngLat) -> float:
        return float(math.dist(a, b))

    def _euclidean_time_h(self, dist_km: float) -> float:
        return dist_km / self.speed_kmh if self.speed_kmh > 0 else float("inf")

    # ---------- mapbox ----------
    def _warm_up_matrix(self) -> None:
        if not self._matrix_client:
            return

        coords = [self.locations[nid] for nid in self._nodes]
        data = self._matrix_client.get_matrix(coords)
        self._durations_s = data["durations"]
        self._distances_m = data["distances"]

    def _mapbox_distance_km(self, a_id: str, b_id: str) -> float:
        if self._distances_m is None:
            self._warm_up_matrix()
        if self._distances_m is None:
            return float("inf")

        ia = self._node_index.get(a_id)
        ib = self._node_index.get(b_id)
        if ia is None or ib is None:
            return float("inf")

        v = self._distances_m[ia][ib]
        return float(v) / 1000.0 if v is not None else float("inf")

    def _mapbox_time_h(self, a_id: str, b_id: str) -> float:
        if self._durations_s is None:
            self._warm_up_matrix()
        if self._durations_s is None:
            return float("inf")

        ia = self._node_index.get(a_id)
        ib = self._node_index.get(b_id)
        if ia is None or ib is None:
            return float("inf")

        v = self._durations_s[ia][ib]
        return float(v) / 3600.0 if v is not None else float("inf")

    # ---------- public API for ACO ----------
    def get_distance_between_nodes(self, node_a_id: str, node_b_id: str) -> float:
        """
        Returns distance in KM
        """
        if node_a_id not in self.locations or node_b_id not in self.locations:
            return float("inf")

        if self.mode == "mapbox":
            return self._mapbox_distance_km(node_a_id, node_b_id)

        # euclidean
        return self._euclidean_distance_km(self.locations[node_a_id], self.locations[node_b_id])

    def get_travel_time_between_nodes(self, node_a_id: str, node_b_id: str) -> float:
        """
        Returns travel time in HOURS
        """
        if node_a_id not in self.locations or node_b_id not in self.locations:
            return float("inf")

        if self.mode == "mapbox":
            return self._mapbox_time_h(node_a_id, node_b_id)

        dist_km = self.get_distance_between_nodes(node_a_id, node_b_id)
        return self._euclidean_time_h(dist_km)
    
    def get_tour_route(
        self,
        ordered_node_ids: List[str],
        include_steps: bool = False,
    ) -> Optional[Dict[str, Any]]:
        """
        Takes an ordered list of node IDs (e.g., ['D_1', 'T_1', 'T_1_D'])
        and returns the Mapbox Directions response containing the route geometry.
        """
        if self.mode != "mapbox":
            print("Warning: Directions API only available in mapbox mode.")
            return None

        # Convert the node IDs back into their actual LngLat coordinates
        route_coords = [self.locations[nid] for nid in ordered_node_ids if nid in self.locations]
        
        if len(route_coords) < 2:
            raise ValueError("Need at least 2 valid nodes to generate a route.")

        if not self._matrix_client:
            return None

        if len(route_coords) <= MAX_COORDS_PER_REQ:
            return self._matrix_client.get_directions(route_coords, steps=include_steps)

        # Directions API over waypoint limit: request in overlapping chunks and stitch.
        chunk_size = MAX_COORDS_PER_REQ
        stride = chunk_size - 1
        chunked_routes: List[Dict[str, Any]] = []

        start = 0
        while start < len(route_coords) - 1:
            end = min(start + chunk_size, len(route_coords))
            chunk = route_coords[start:end]
            if len(chunk) < 2:
                break

            response = self._matrix_client.get_directions(chunk, steps=include_steps)
            routes = response.get("routes", [])
            if not routes:
                raise RuntimeError("Mapbox Directions response missing routes for chunk.")
            chunked_routes.append(routes[0])

            if end == len(route_coords):
                break
            start += stride

        stitched_coordinates: List[List[float]] = []
        total_distance = 0.0
        total_duration = 0.0
        for route in chunked_routes:
            geometry = route.get("geometry", {}) or {}
            coordinates = geometry.get("coordinates", []) or []
            if not coordinates:
                continue

            if not stitched_coordinates:
                stitched_coordinates.extend(coordinates)
            else:
                # Avoid duplicating the overlap point between adjacent chunks.
                if stitched_coordinates[-1] == coordinates[0]:
                    stitched_coordinates.extend(coordinates[1:])
                else:
                    stitched_coordinates.extend(coordinates)

            total_distance += float(route.get("distance") or 0.0)
            total_duration += float(route.get("duration") or 0.0)

        stitched_response: Dict[str, Any] = {
            "code": "Ok",
            "chunked": True,
            "routes": [
                {
                    "geometry": {"type": "LineString", "coordinates": stitched_coordinates},
                    "distance": total_distance,
                    "duration": total_duration,
                }
            ],
        }
        if include_steps and chunked_routes:
            first_legs = chunked_routes[0].get("legs", []) or []
            if first_legs:
                stitched_response["routes"][0]["legs"] = first_legs
        return stitched_response
