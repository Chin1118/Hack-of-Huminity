import numpy as np
from scipy.spatial import KDTree

class TaskDispatcher:
    def __init__(self, drivers):

        self.available_drivers = [d for d in drivers if d["available"]]
        self.drivers_locations = np.array([d["start_location"] for d in self.available_drivers])
        
        self.tree = KDTree(self.drivers_locations)

    def find_target_drivers(self, task):
        
        pickup_location = task['pickup']['location'] # [lat, lon]

        k = min(3, len(self.available_drivers))
        indices = self.tree.query(pickup_location, k=k)[1]

        if k == 1:
            indices = [indices]

        target_drivers = [self.available_drivers[i] for i in indices]
        return target_drivers