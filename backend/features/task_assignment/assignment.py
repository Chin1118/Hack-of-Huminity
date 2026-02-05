import math

def assign_task_to_driver(task, drivers):
    """
    MOCK IMPLEMENTATION of Voronoi Assignment.
    Assigns the task to the closest driver based on Euclidean distance.
    """
    best_driver_id = None
    min_dist = float('inf')

    tx, ty = task.pickup_location

    for driver in drivers:
        dx, dy = driver.start_location
        dist = math.sqrt((tx - dx)**2 + (ty - dy)**2)
        
        if dist < min_dist:
            min_dist = dist
            best_driver_id = driver.id
            
    return best_driver_id
