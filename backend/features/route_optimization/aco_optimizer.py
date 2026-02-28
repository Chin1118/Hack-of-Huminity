from __future__ import annotations

import random
from typing import Any, Dict, List, Tuple

from backend.features.route_optimization.cost_calculator import (
    calculate_carbon_emission,
    calculate_heuristic,
    calculate_total_cost,
)
from backend.models.emission import EmissionModel
from backend.models.pheromone import (
    get_pheromone_value,
    init_pheromone_matrix,
    save_pheromone_matrix,
    update_pheromone_matrix,
)
from backend.utils.road_network import RoadNetwork


class ACOOptimizer:
    def __init__(
        self,
        driver,
        tasks,
        road_mode: str = "mapbox",
        pheromone_matrix: Dict[str, Dict[str, float]] | None = None,
        alpha: float = 1.0,
        beta: float = 2.0,
        rho: float = 0.1,
        q: float = 100.0,
        n_ants: int = 10,
        n_iterations: int = 50,
        cost_alpha: float = 0.5,
        cost_beta: float = 0.5,
    ):
        self.driver = driver
        self.tasks = tasks
        self.alpha = alpha
        self.beta = beta
        self.rho = rho
        self.q = q
        self.n_ants = n_ants
        self.n_iterations = n_iterations
        self.cost_alpha = cost_alpha
        self.cost_beta = cost_beta

        self.driver_id = str(driver.id)
        self.driver_node = f"D_{self.driver_id}"

        self.matrix = RoadNetwork(drivers=[driver], tasks=tasks, mode=road_mode)
        self.emission_model = getattr(driver, "emission_model", None) or EmissionModel()

        if pheromone_matrix:
            self.pheromone_matrix = pheromone_matrix
        else:
            self.pheromone_matrix = init_pheromone_matrix([driver], tasks)

        self.pickup_nodes = {f"T_{t.id}": t for t in tasks}
        self.dropoff_nodes = {f"T_{t.id}_D": t for t in tasks}

        self.all_nodes = set([self.driver_node])
        self.all_nodes.update(self.pickup_nodes.keys())
        self.all_nodes.update(self.dropoff_nodes.keys())

    def _get_heuristic(self, from_node: str, to_node: str) -> float:
        dist = self.matrix.get_distance_between_nodes(from_node, to_node)
        co2_emission = calculate_carbon_emission(
            self.emission_model,
            dist,
            self.driver.vehicle_type,
        )
        return calculate_heuristic(co2_emission)

    def _calculate_path_cost(self, path: List[str]) -> Tuple[float, float, float]:
        total_co2 = 0.0
        total_time = 0.0
        if not path:
            return 0.0, 0.0, 0.0

        for i in range(len(path) - 1):
            u, v = path[i], path[i + 1]
            dist = self.matrix.get_distance_between_nodes(u, v)
            time = self.matrix.get_travel_time_between_nodes(u, v)
            total_time += time
            total_co2 += calculate_carbon_emission(
                self.emission_model,
                dist,
                self.driver.vehicle_type,
            )

        total_cost = calculate_total_cost(
            self.cost_alpha,
            self.cost_beta,
            total_time,
            total_co2,
        )
        return total_cost, total_time, total_co2

    def solve(self) -> Dict:
        best_path: List[str] = []
        best_cost = float("inf")
        best_metrics: Dict[str, float] = {}

        for _ in range(self.n_iterations):
            ants_paths: List[List[str]] = []
            ants_costs: List[float] = []

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

            if ants_paths:
                self._update_pheromones(ants_paths, ants_costs)

        return {
            "driver_id": self.driver_id,
            "best_path_nodes": best_path,
            "metrics": best_metrics,
        }

    def _construct_solution(self) -> List[str]:
        path = [self.driver_node]
        current_node = self.driver_node
        visited = {self.driver_node}
        target_length = len(self.all_nodes)

        while len(visited) < target_length:
            feasible_neighbors: List[str] = []

            for t_node in self.pickup_nodes:
                if t_node not in visited:
                    feasible_neighbors.append(t_node)

            for d_node_id, task in self.dropoff_nodes.items():
                pickup_node_id = f"T_{task.id}"
                if d_node_id not in visited and pickup_node_id in visited:
                    feasible_neighbors.append(d_node_id)

            if not feasible_neighbors:
                break

            next_node = self._select_next_node(current_node, feasible_neighbors)
            path.append(next_node)
            visited.add(next_node)
            current_node = next_node

        return path

    def _select_next_node(self, current_node: str, neighbors: List[str]) -> str:
        if len(neighbors) == 1:
            return neighbors[0]

        attractions: List[float] = []
        for neighbor in neighbors:
            tau = get_pheromone_value(self.pheromone_matrix, current_node, neighbor, default=1.0)
            if tau <= 0:
                tau = 1e-6

            eta = self._get_heuristic(current_node, neighbor)
            if eta <= 0:
                eta = 1e-6

            attractions.append((tau ** self.alpha) * (eta ** self.beta))

        total_attraction = sum(attractions)
        if total_attraction <= 0:
            return random.choice(neighbors)

        probabilities = [v / total_attraction for v in attractions]
        return random.choices(neighbors, weights=probabilities, k=1)[0]

    def _update_pheromones(self, ants_paths: List[List[str]], ants_costs: List[float]) -> None:
        self.pheromone_matrix = update_pheromone_matrix(self.pheromone_matrix, self.rho)

        for path, cost in zip(ants_paths, ants_costs):
            if cost <= 0:
                continue
            deposit = self.q / cost
            for i in range(len(path) - 1):
                u, v = path[i], path[i + 1]
                if u not in self.pheromone_matrix:
                    self.pheromone_matrix[u] = {}
                if v not in self.pheromone_matrix[u]:
                    self.pheromone_matrix[u][v] = 0.0
                self.pheromone_matrix[u][v] += deposit

        save_pheromone_matrix(self.pheromone_matrix)


def _task_cost_for_driver(optimizer: ACOOptimizer, task: Any) -> Tuple[float, float, float]:
    driver_node = optimizer.driver_node
    pickup_node = f"T_{task.id}"
    dropoff_node = f"T_{task.id}_D"

    distance_to_pickup = optimizer.matrix.get_distance_between_nodes(driver_node, pickup_node)
    distance_pickup_to_dropoff = optimizer.matrix.get_distance_between_nodes(
        pickup_node,
        dropoff_node,
    )
    total_distance = distance_to_pickup + distance_pickup_to_dropoff

    time_to_pickup = optimizer.matrix.get_travel_time_between_nodes(driver_node, pickup_node)
    time_pickup_to_dropoff = optimizer.matrix.get_travel_time_between_nodes(
        pickup_node,
        dropoff_node,
    )
    total_time = time_to_pickup + time_pickup_to_dropoff

    total_co2 = calculate_carbon_emission(
        optimizer.emission_model,
        total_distance,
        optimizer.driver.vehicle_type,
    )
    total_cost = calculate_total_cost(
        optimizer.cost_alpha,
        optimizer.cost_beta,
        total_time,
        total_co2,
    )
    return total_cost, total_time, total_co2


def run_multi_driver_aco(
    drivers: List[Any],
    tasks: List[Any],
    candidate_map: Dict[str, List[str]],
    road_mode: str = "mapbox",
    pheromone_matrix: Dict[str, Dict[str, float]] | None = None,
) -> Dict[str, Any]:
    tasks_by_id = {str(task.id): task for task in tasks}
    scored_assignments: List[Dict[str, float | str]] = []
    per_driver_results: Dict[str, Dict[str, Any]] = {}

    for driver in drivers:
        driver_id = str(driver.id)
        candidate_task_ids = candidate_map.get(driver_id, [])
        candidate_tasks = [
            tasks_by_id[task_id]
            for task_id in candidate_task_ids
            if task_id in tasks_by_id
        ]
        if not candidate_tasks:
            per_driver_results[driver_id] = {
                "driver_id": driver_id,
                "best_path_nodes": [],
                "metrics": {},
            }
            continue

        optimizer = ACOOptimizer(
            driver=driver,
            tasks=candidate_tasks,
            road_mode=road_mode,
            pheromone_matrix=pheromone_matrix,
        )
        result = optimizer.solve()
        per_driver_results[driver_id] = result

        for task in candidate_tasks:
            total_cost, total_time, total_co2 = _task_cost_for_driver(optimizer, task)
            scored_assignments.append(
                {
                    "driver_id": driver_id,
                    "task_id": str(task.id),
                    "total_cost": float(total_cost),
                    "time": float(total_time),
                    "co2": float(total_co2),
                }
            )

    return {
        "per_driver_results": per_driver_results,
        "scored_assignments": scored_assignments,
    }
