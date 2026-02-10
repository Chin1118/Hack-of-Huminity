import numpy as np
from scipy.spatial import KDTree

class TaskAssigner:
    def __init__(self, tasks):
        
        self.pending_tasks = [t for t in tasks if t.get("status") == "pending"]
        
        if not self.pending_tasks:
            self.task_locations = np.empty((0, 2))
            self.tree = None
        else:
            self.task_locations = np.array([t['pickup']['location'] for t in self.pending_tasks])
            self.tree = KDTree(self.task_locations)

    def get_tasks_for_driver(self, driver, max_tasks=3):

        if self.tree is None:
            return []

        driver_location = driver['start_location'] # [lat, lon]

        k = min(max_tasks, len(self.pending_tasks))
        indices = self.tree.query(driver_location, k=k)

        if k == 1:
            indices = [indices]

        nearby_tasks = [self.pending_tasks[i] for i in indices]
        return nearby_tasks
