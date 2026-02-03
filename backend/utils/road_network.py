import math
from typing import Tuple, List, Dict

class RoadNetwork:
    def __init__(self, drivers: List, tasks: List, speed: float = 50.0):
        """
        Road network initialization
        
        Args:
            drivers: List of Driver objects
            tasks: List of Task objects
            speed: Average speed (km/h), default 50 km/h
        """
        self.speed = speed
        self.locations: Dict[str, Tuple[float, float]] = {}
        
        #Add driver nodes
        for driver in drivers:
            self.locations[f"D_{driver.id}"] = driver.start_location
            
        #Add task nodes
        for task in tasks:
            self.locations[f"T_{task.id}"] = task.pickup_location         #pick up point
            self.locations[f"T_{task.id}_D"] = task.dropoff_location      #drop off point
    
    def distance(self, a: Tuple[float, float], b: Tuple[float, float]) -> float:
        """
        Calculate Euclidean distance (km)
        """
        return math.dist(a, b)
    
    def travel_time(self, a: Tuple[float, float], b: Tuple[float, float]) -> float:
        """
        Calculate travel time (hours)
        """
        distance_km = self.distance(a, b)
        return distance_km / self.speed if self.speed > 0 else float('inf')
    
    #for ACO
    def get_all_nodes(self) -> List[str]:
        """
        Get a list of all node IDs
        """
        return list(self.locations.keys())
    
    def get_location(self, node_id: str) -> Tuple[float, float]:
        """
        Get location coordinates based on node ID
        """
        return self.locations.get(node_id, (0.0, 0.0))
    
    def get_distance_between_nodes(self, node_a_id: str, node_b_id: str) -> float:
        """
        Calculate the distance between two nodes
        """
        if node_a_id in self.locations and node_b_id in self.locations:
            return self.distance(self.locations[node_a_id], self.locations[node_b_id])
        return float('inf')