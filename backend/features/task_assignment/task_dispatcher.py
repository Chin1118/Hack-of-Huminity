import numpy as np
from scipy.spatial import KDTree
from api.converters.driver import update_driver

class TaskAssigner:
    def __init__(self, tasks):
        
        self.pending_tasks = [t for t in tasks if t.get("status") != "assigned"]
        
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
        distances, indices = self.tree.query(driver_location, k=k)

        if k == 1:
            indices = [indices]

        nearby_tasks = [self.pending_tasks[i]['id'] for i in indices]
        return nearby_tasks

    def update_task_list(self, driver, max_tasks=3):
       
        tasks = self.get_tasks_for_driver(driver, max_tasks=max_tasks)
        driver['task_list'] = tasks
        
        update_driver(driver)

def assign_tasks_to_drivers(drivers, tasks, max_tasks=3):

    assigner = TaskAssigner(tasks)
    
    for driver in drivers:
       
        if driver.get("available") is True:
            assigner.update_task_list(driver, max_tasks=max_tasks)
            
            """
            print(f"Updated Driver {driver.get('id', 'Unknown')}: Assigned {len(driver.get('task_list', []))} tasks.")
            print(driver['task_list'])

if __name__ == "__main__":
    assign_tasks_to_drivers([
  {
    "id": 1,
    "start_location": [
      1.5,
      2.3
    ],
    "vehicle_type": "fuel",
    "capacity": 500.0,
    "available": True
  },
  {
    "id": 2,
    "start_location": [
      15.2,
      15.8
    ],
    "vehicle_type": "ev",
    "capacity": 300.0,
    "available": True
  }
], [
    {
      "id": 101,
      "weight": 10.0,
      "status": "pending",
      "pickup": {
        "location": [
          1.0,
          2.0
        ],
        "time_window": [
          8.0,
          10.0
        ]
      },
      "dropoff": {
        "location": [
          3.0,
          4.0
        ],
        "time_window": [
          11.0,
          13.0
        ]
      }
    },
    {
      "id": 102,
      "weight": 20.0,
      "status": "pending",
      "pickup": {
        "location": [
          10.0,
          10.0
        ],
        "time_window": [
          9.0,
          11.0
        ]
      },
      "dropoff": {
        "location": [
          6.0,
          8.0
        ],
        "time_window": [
          14.0,
          16.0
        ]
      }
    }, {
      "id": 103,
      "weight": 20.0,
      "status": "pending",
      "pickup": {
        "location": [
          15.0,
          15.0
        ],
        "time_window": [
          9.0,
          11.0
        ]
      },
      "dropoff": {
        "location": [
          6.0,
          8.0
        ],
        "time_window": [
          14.0,
          16.0
        ]
      }
    }, {
      "id": 104,
      "weight": 20.0,
      "status": "pending",
      "pickup": {
        "location": [
          20.0,
          20.0
        ],
        "time_window": [
          9.0,
          11.0
        ]
      },
      "dropoff": {
        "location": [
          6.0,
          8.0
        ],
        "time_window": [
          14.0,
          16.0
        ]
      }
    }, {
      "id": 105,
      "weight": 20.0,
      "status": "pending",
      "pickup": {
        "location": [
          25.0,
          25.0
        ],
        "time_window": [
          9.0,
          11.0
        ]
      },
      "dropoff": {
        "location": [
          6.0,
          8.0
        ],
        "time_window": [
          14.0,
          16.0
        ]
      }
    }
  ])
"""