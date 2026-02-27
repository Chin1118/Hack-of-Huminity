import json
import os
from typing import List, Optional
from backend.models.task import Task

# JSON file path
TASKS_JSON_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "data",
    "tasks.json"
)

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
    if not os.path.exists(TASKS_JSON_PATH): # Check if the JSON file exists
        return []
    
    try:
        with open(TASKS_JSON_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            return [json_to_task(item) for item in data]
    except (json.JSONDecodeError, KeyError) as e:
        raise ValueError(f"JSON file format error: {e}")


# Save tasks to JSON file
def save_tasks(tasks: List[Task]) -> None:
    os.makedirs(os.path.dirname(TASKS_JSON_PATH), exist_ok=True) # Create the directory if it doesn't exist
    
    data = [task_to_json(task) for task in tasks]
    
    with open(TASKS_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


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
