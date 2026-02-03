
#Load and validate JSON data into Driver and Task objects.
import json
from typing import Tuple, List
from models.driver import Driver
from models.task import Task

def load_system_data(file_path: str) -> Tuple[List[Driver], List[Task]]:
    """
    Loading system data from a JSON file

    Args:
        file_path: JSON file path
    
    Returns:
        (drivers, tasks) tuple
        
    Raises:
        FileNotFoundError: File does not exist
        json.JSONDecodeError: JSON format error
        ValueError: Missing required fields
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        #Validate required fields
        if "drivers" not in data:
            raise ValueError("JSON file must contain 'drivers' field")
        if "tasks" not in data:
            raise ValueError("JSON file must contain 'tasks' field")
        
        #Create Driver objects list
        drivers = []
        for driver_data in data["drivers"]:
            #Validate driver data format
            required_fields = ["id", "start_location", "vehicle_type"]

            for field in required_fields:
                if field not in driver_data:
                    raise ValueError(f"Driver data missing required field: {field}")
            drivers.append(Driver.from_json(driver_data))
        
        #Create Task objects list
        tasks = []
        for task_data in data["tasks"]:
            #Validate task data format
            required_fields = ["id", "weight", "pickup", "dropoff"]

            for field in required_fields:
                if field not in task_data:
                    raise ValueError(f"Task data missing required field: {field}")
            
            #Validate pickup and dropoff sub-fields
            if "location" not in task_data["pickup"] or "time_window" not in task_data["pickup"]:
                raise ValueError("Task pickup data missing 'location' or 'time_window'")
            if "location" not in task_data["dropoff"] or "time_window" not in task_data["dropoff"]:
                raise ValueError("Task dropoff data missing 'location' or 'time_window'")
            
            tasks.append(Task.from_json(task_data))
        
        return drivers, tasks
        
    except FileNotFoundError:
        print(f"Error: File {file_path} does not exist")
        raise
    except json.JSONDecodeError as e:
        print(f"Error: File {file_path} is not a valid JSON format")
        print(f"Error details: {e}")
        raise
    except Exception as e:
        print(f"Error loading data: {e}")
        raise