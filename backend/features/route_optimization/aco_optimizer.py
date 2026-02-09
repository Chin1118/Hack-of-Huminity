from typing import List, Dict, Tuple, Set, Optional
import random
from backend.api.schemas.driver import DriverBase
from backend.models.task import Task
from backend.utils.pheromone import get_pheromone_value, update_pheromone_matrix, save_pheromone_matrix
from backend.features.route_optimization.cost_calculator import (
    calculate_distance, calculate_carbon_emission, calculate_time, calculate_heuristic, calculate_total_cost
)

class ACOOptimizer:
    def __init__(self, 
                 driver: DriverBase, 
                 tasks: List[Task], 
                 pheromone_matrix: Dict[str, Dict[str, float]],
                 alpha: float = 1.0,        # Pheromone importance
                 beta: float = 2.0,         # Heuristic importance
                 rho: float = 0.1,          # Evaporation rate
                 q: float = 100.0,          # Pheromone deposit amount
                 n_ants: int = 10,
                 n_iterations: int = 50,
                 cost_alpha: float = 0.5,   # Time cost weight
                 cost_beta: float = 0.5,    # CO2 cost weight
                 epsilon: float = 0.01      # Avoid division by zero
                 ):
        
        self.driver = driver
        self.tasks = tasks
        self.pheromone_matrix = pheromone_matrix
        self.alpha = alpha
        self.beta = beta
        self.rho = rho
        self.q = q
        self.n_ants = n_ants
        self.n_iterations = n_iterations
        self.cost_alpha = cost_alpha
        self.cost_beta = cost_beta
        self.epsilon = epsilon
        
        self.driver_id = driver.id
        self.driver_node = f"D_{self.driver_id}"

        self.pickup_nodes = {f"T_{t.id}": t for t in tasks}
        self.dropoff_nodes = {f"T_{t.id}_D": t for t in tasks}
        
        # Identify all nodes for completeness check
        # Node set: {D_id, T_1, T_1_D, T_2, T_2_D, ...}
        self.all_nodes = set([self.driver_node])
        self.all_nodes.update(self.pickup_nodes.keys())
        self.all_nodes.update(self.dropoff_nodes.keys())
        
        self.locations = {self.driver_node: driver.start_location}
        for t in tasks:
            self.locations[f"T_{t.id}"] = t.pickup_location
            self.locations[f"T_{t.id}_D"] = t.dropoff_location

    def _get_heuristic(self, from_node: str, to_node: str) -> float:
        loc1 = self.locations[from_node]
        loc2 = self.locations[to_node]
        dist = calculate_distance(loc1, loc2)
        co2_emission = calculate_carbon_emission(dist, self.driver.vehicle_type)
        return calculate_heuristic(co2_emission)

    # Calculate total cost of a path. Returns (total_cost, total_time, total_co2)    
    def _calculate_path_cost(self, path: List[str]) -> Tuple[float, float, float]:
        total_dist = 0.0
        total_co2 = 0.0
        
        if not path:
            return 0.0, 0.0, 0.0

        for i in range(len(path) - 1):
            u, v = path[i], path[i+1]
            dist = calculate_distance(self.locations[u], self.locations[v])
            total_dist += dist
            total_co2 += calculate_carbon_emission(dist, self.driver.vehicle_type)
            
        total_time = calculate_time(total_dist) # Simple time calculation
        total_cost = calculate_total_cost(total_time, total_co2, self.cost_alpha, self.cost_beta)
        
        return total_cost, total_time, total_co2

    def solve(self) -> Dict:
        best_path = []
        best_cost = float('inf')
        best_metrics = {}

        for iteration in range(self.n_iterations):
            ants_paths = []
            ants_costs = []
            
            for _ in range(self.n_ants):
                path = self._construct_solution()
                if not path:
                     continue

                cost, time, co2 = self._calculate_path_cost(path)
                
                ants_paths.append(path)
                ants_costs.append(cost)
                
                if cost < best_cost:
                    best_path = path
                    best_cost = cost
                    best_metrics = {"time": time, "co2": co2, "total_cost": cost}

            # Update Pheromones
            if ants_paths:
                self._update_pheromones(ants_paths, ants_costs)

        return {
            "driver_id": self.driver_id,
            "best_path_nodes": best_path,
            "metrics": best_metrics
        }

    def _construct_solution(self) -> List[str]:
        path = [self.driver_node]
        current_node = self.driver_node
        visited = set([self.driver_node])
        
        target_length = len(self.all_nodes)
        
        while len(visited) < target_length:
            feasible_neighbors = []
            
            for t_node in self.pickup_nodes:
                if t_node not in visited:
                    feasible_neighbors.append(t_node)
            
            for d_node_id, task in self.dropoff_nodes.items():
                pickup_node_id = f"T_{task.id}"
                if d_node_id not in visited and pickup_node_id in visited:
                     feasible_neighbors.append(d_node_id)
            
            if not feasible_neighbors:
                break 
            
            # Select next node based on probability
            next_node = self._select_next_node(current_node, feasible_neighbors)
            
            path.append(next_node)
            visited.add(next_node)
            current_node = next_node
            
        return path

    def _select_next_node(self, current_node: str, neighbors: List[str]) -> str:
        # If only one neighbor, return it directly
        if len(neighbors) == 1:
            return neighbors[0]

        probabilities = []
        attractions = []
        
        for neighbor in neighbors:
            # Get Pheromone Tau
            tau = get_pheromone_value(self.pheromone_matrix, current_node, neighbor, default=1.0)
            if tau <= 0: tau = 1e-6 # Safety
            
            # Get Heuristic Eta
            eta = self._get_heuristic(current_node, neighbor)
            if eta <= 0: eta = 1e-6 # Safety

            v = (tau ** self.alpha) * (eta ** self.beta)
            attractions.append(v)
        
        total_attraction = sum(attractions)
        
        if total_attraction == 0:
            # Fallback to random if all attractions are zero
            return random.choice(neighbors)
            
        probabilities = [v / total_attraction for v in attractions]
        
        return random.choices(neighbors, weights=probabilities, k=1)[0]

    def _update_pheromones(self, ants_paths: List[List[str]], ants_costs: List[float]):
        # update_pheromone_matrix modifies in-place and returns
        self.pheromone_matrix = update_pheromone_matrix(self.pheromone_matrix, self.rho)
        
        for path, cost in zip(ants_paths, ants_costs):
            if cost <= 0: continue
            
            deposit = self.q / cost
            for i in range(len(path) - 1):
                u, v = path[i], path[i+1]
                
                if u not in self.pheromone_matrix:
                    self.pheromone_matrix[u] = {}
                if v not in self.pheromone_matrix[u]:
                    self.pheromone_matrix[u][v] = 0.0 
                
                self.pheromone_matrix[u][v] += deposit
        
        # Save persistence
        save_pheromone_matrix(self.pheromone_matrix)
