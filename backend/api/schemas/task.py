from typing import Optional

from pydantic import BaseModel, Field


class TaskBase(BaseModel):
    pickup_location: list[float] = Field(
        ...,
        min_length=2,
        max_length=2,
        description="Pickup location [lng, lat]",
    )
    dropoff_location: list[float] = Field(
        ...,
        min_length=2,
        max_length=2,
        description="Dropoff location [lng, lat]",
    )
    note: Optional[str] = Field(default=None, description="Task note")
    type: Optional[str] = Field(default=None, description="Task type")
    status: Optional[str] = Field(default=None, description="Task status")


class TaskCreate(TaskBase):
    driver_id: Optional[str] = None


class TaskUpdate(BaseModel):
    pickup_location: Optional[list[float]] = Field(default=None, min_length=2, max_length=2)
    dropoff_location: Optional[list[float]] = Field(default=None, min_length=2, max_length=2)
    note: Optional[str] = None
    type: Optional[str] = None
    status: Optional[str] = None


class TaskArriveRequest(BaseModel):
    current_location: list[float] = Field(
        ...,
        min_length=2,
        max_length=2,
        description="Current location [lng, lat]",
    )
    radius_m: float = Field(
        default=120.0,
        gt=0,
        le=1000.0,
        description="Arrival radius in meters",
    )


class TaskResponse(TaskBase):
    id: str
    driver_id: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class TaskIdsResponse(BaseModel):
    task_ids: list[str]


class TaskAssignmentItem(BaseModel):
    task_id: str
    task_name: str


class DriverTaskAssignments(BaseModel):
    driver_id: str
    driver_name: str
    tasks: list[TaskAssignmentItem]


class TodayAssignmentsResponse(BaseModel):
    date_utc: str
    total_assigned_tasks: int
    assignments: list[DriverTaskAssignments]


class PendingTasksCountResponse(BaseModel):
    pending_tasks: int
