import json
from backend.models.driver import Driver
from backend.models.task import Task
from backend.features.realtime.dispatcher import Dispatcher

def load_data():
    with open("backend/utils/data.json", "r") as f:
        data = json.load(f)
    
    drivers = [Driver.from_json(d) for d in data["drivers"]]
    tasks = [Task.from_json(t) for t in data["tasks"]]
    
    return drivers, tasks

def main():
    print("=== Green Delivery System Simulation (Task 10) ===")
    
    # 1. Init System
    drivers, tasks = load_data()
    print(f"Loaded {len(drivers)} drivers and {len(tasks)} tasks.")
    
    dispatcher = Dispatcher(drivers)
    
    # 2. Simulate Real-Time Task Arrival
    # In a real app, this would be an API endpoint or socket event
    for task in tasks:
        # Simulate delay? time.sleep(1)
        dispatcher.handle_new_task(task)
        print("-" * 30)

    # 3. Final Summary
    print("\n=== Final Schedule ===")
    routes = dispatcher.get_all_routes()
    total_co2_impact = 0.0 # This would be summed up properly in a real run
    
    for driver_id, route in routes.items():
        print(f"Driver {driver_id}: {[t.id for t in route]}")

if __name__ == "__main__":
    main()
