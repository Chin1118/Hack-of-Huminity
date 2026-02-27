from __future__ import annotations
import math
from typing import Tuple, List, Dict, Any, Optional, Literal
import requests
from backend.config import MAPBOX_TOKEN
import folium
from typing import Any

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

    def get_directions(self, coords: List[LngLat]) -> Dict[str, Any]:
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
            "steps": "false"          # set to 'true' if you want turn-by-turn instructions
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
    
    def get_tour_route(self, ordered_node_ids: List[str]) -> Optional[Dict[str, Any]]:
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

        # If the tour is longer than Mapbox's 25 waypoint limit, you either 
        # need to chunk the requests and stitch them together, or drop intermediate 
        # points and only route the key stops. For now, we'll enforce the limit:
        if len(route_coords) > MAX_COORDS_PER_REQ:
             raise ValueError(f"Tour too long for a single Mapbox request ({len(route_coords)} > 25). Chunking required.")

        if not self._matrix_client:
            return None

        return self._matrix_client.get_directions(route_coords)
    
    
""" 
# 1. Quick mock classes just to test the initialization
class MockDriver:
    def __init__(self, id, lng, lat):
        self.id = id
        self.start_location = (lng, lat)

class MockTask:
    def __init__(self, id, p_lng, p_lat, d_lng, d_lat):
        self.id = id
        self.pickup_location = (p_lng, p_lat)
        self.dropoff_location = (d_lng, d_lat)


if __name__ == "__main__":
    # 2. Setup some test coordinates (Replace with your actual test locations)
    # E.g., San Francisco coordinates
    d1 = MockDriver("1", -122.4194, 37.7749)
    t1 = MockTask("1", -122.4312, 37.7739, -122.4000, 37.7900)

    # 3. Initialize your network
    # Make sure your MAPBOX_TOKEN is loaded in your environment/config
    network = RoadNetwork(
        drivers=[d1], 
        tasks=[t1], 
        mode="mapbox"
    )

    # 4. Get the route for a mock tour: Driver 1 -> Task 1 Pickup -> Task 1 Dropoff
    tour = ["D_1", "T_1", "T_1_D"]
    route_data = network.get_tour_route(tour)

    if route_data and "routes" in route_data and len(route_data["routes"]) > 0:
        # Extract the GeoJSON geometry Mapbox returned
        geometry = route_data["routes"][0]["geometry"]
        
        # Mapbox returns [longitude, latitude], but Folium centers on [latitude, longitude]
        start_lon, start_lat = geometry["coordinates"][0]
        
        # Create an interactive map centered at the start location
        m = folium.Map(location=[start_lat, start_lon], zoom_start=13)
        
        # Add the route line to the map
        folium.GeoJson(
            geometry,
            name="ACO Tour Route",
            style_function=lambda x: {'color': 'blue', 'weight': 5, 'opacity': 0.8}
        ).add_to(m)
        
        # Add markers for the stops
        for node_id in tour:
            lon, lat = network.get_location(node_id)
            folium.Marker([lat, lon], popup=node_id).add_to(m)
        
        # Save to an HTML file and open it!
        m.save("test_route.html")
        print("Map saved to test_route.html! Open this file in your browser.")
    else:
        print("Failed to get route data:", route_data)
"""