from backend.persistence.json_repository import JSONRepository

def test_persistence():
    repo = JSONRepository()

    driver = {
        "id": 1,
        "start_location": (0.0, 0.0),
        "vehicle_type": "ev",
        "capacity": 100.0,
        "available": True
    }

    task = {
        "id": 101,
        "pickup_location": (2.0, 2.0),
        "pickup_time_window": (8.0, 10.0),
        "dropoff_location": (5.0, 5.0),
        "dropoff_time_window": (9.0, 11.0),
        "weight": 10.0
    }

    route_result = {
        "driver_id": 1,
        "best_path_nodes": ["D_1", "T_101", "T_101_D"],
        "metrics": {"time": 0.1, "co2": 0.01, "total_cost": 0.05}
    }

    repo.save_driver(driver)
    repo.save_task(task)
    repo.save_route_result(route_result)

    loaded_drivers = repo.load_drivers()
    loaded_tasks = repo.load_tasks()
    loaded_routes = repo.load_routes()

    print("Drivers loaded:", loaded_drivers)
    print("Tasks loaded:", loaded_tasks)
    print("Routes loaded:", loaded_routes)

if __name__ == "__main__":
    test_persistence()