from typing import List, Optional
import json

from backend.models.task import Task
from backend.data_access.data_provider import get_data_provider

# Convert JSON dict to Task object
def json_to_task(data: dict) -> Task:
    return Task(
        id=data["id"],
        pickup_location=tuple(data["pickup_location"]),
        dropoff_location=tuple(data["dropoff_location"]),
        weight=data.get("weight", 0.0),
        status=data.get("status", "unassigned")
    )


# Convert Task object to JSON dict
def task_to_json(task: Task) -> dict:
    return {
        "id": task.id,
        "pickup_location": list(task.pickup_location),
        "dropoff_location": list(task.dropoff_location),
        "weight": task.weight,
        "status": task.status
    }


# Load all tasks from JSON file
def load_tasks() -> List[Task]:
    try:
        data = get_data_provider().load_list("tasks")
        return [json_to_task(item) for item in data]
    except (json.JSONDecodeError, KeyError) as e:
        raise ValueError(f"JSON file format error: {e}")


# Save tasks to JSON file
def save_tasks(tasks: List[Task]) -> None:
    data = [task_to_json(task) for task in tasks]
    get_data_provider().save_list("tasks", data)


# Find a single task by ID
def find_task_by_id(task_id: int) -> Optional[Task]: # May use in validation
    tasks = load_tasks()
    for task in tasks:
        if task.id == task_id:
            return task
    return None


# Add a new task
def add_task(task: Task) -> Task:
    tasks = load_tasks()
    
    # Auto-generate ID (find max ID + 1)
    if tasks:
        max_id = max(d.id for d in tasks)
        task.id = max_id + 1
    else:
        task.id = 1
    
    tasks.append(task)
    save_tasks(tasks)
    return task


# Update a task
def update_task(task_id: int, updated_task: Task) -> Optional[Task]:
    tasks = load_tasks()
    
    for i, task in enumerate(tasks):
        if task.id == task_id:
            # Keep ID unchanged
            updated_task.id = task_id
            tasks[i] = updated_task
            save_tasks(tasks)
            return updated_task
    
    return None


# Delete a task
def delete_task(task_id: int) -> bool:
    tasks = load_tasks()
    
    for i, task in enumerate(tasks):
        if task.id == task_id:
            tasks.pop(i)
            save_tasks(tasks)
            return True
    
    return False
