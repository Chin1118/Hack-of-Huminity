from backend.features.task_assignment.assignment import assign_task_to_driver
from backend.features.path_optimization.optimization import optimize_driver_route
from backend.features.carbon.emission import calculate_carbon_emission

class Dispatcher:
    def __init__(self, drivers):
        self.drivers = {d.id: d for d in drivers}
        self.driver_routes = {d.id: [] for d in drivers} # Map driver_id -> List[Task]

    def handle_new_task(self, task):
        """
        1. Find best driver (Task 2)
        2. Assign task
        3. Optimize route (Task 3)
        4. Calculate impact (Task 5)
        """
        print(f"[Dispatcher] New Task {task.id} received.")
        
        # 1. Assignment
        available_drivers = [d for d in self.drivers.values() if d.available]
        if not available_drivers:
            print("[Dispatcher] No available drivers!")
            return

        best_driver_id = assign_task_to_driver(task, available_drivers)
        best_driver = self.drivers[best_driver_id]
        print(f"[Dispatcher] Assigned Task {task.id} to Driver {best_driver_id} ({best_driver.vehicle_type}).")

        # 2. Add to route
        current_route = self.driver_routes[best_driver_id]
        current_route.append(task)

        # 3. Optimization (Partial Recalculation)
        new_route = optimize_driver_route(best_driver, current_route)
        self.driver_routes[best_driver_id] = new_route

        # 4. Carbon Calculation (Impact Analysis)
        # Simplify: Calculate emission for the *last* leg of the trip
        # In real ACO, we would calc total route cost.
        if len(new_route) == 1:
            prev_loc = best_driver.start_location
        else:
            prev_loc = new_route[-2].dropoff_location # Simplified: previous task dropoff
        
        curr_task = new_route[-1]
        
        # Distance calc (Euclidean for now)
        dist = ((curr_task.pickup_location[0] - prev_loc[0])**2 + 
                (curr_task.pickup_location[1] - prev_loc[1])**2)**0.5
        
        # Estimate trip time (assume 30km/h avg speed)
        time_est = dist / 30.0 

        co2 = calculate_carbon_emission(
            best_driver.vehicle_type,
            distance_km=dist,
            time_hours=time_est,
            payload_weight=curr_task.weight
        )
        
        print(f"[Dispatcher] Route Updated. Added Leg CO2: {co2:.2f} kg")

    def get_all_routes(self):
        return self.driver_routes
