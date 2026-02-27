from pydantic import BaseModel, Field
from typing import Tuple, Optional


class TaskBase(BaseModel):
    pickup_location: Tuple[float, float] = Field(..., description="Pickup location (lat, lon)")
    dropoff_location: Tuple[float, float] = Field(..., description="Dropoff location (lat, lon)")
    weight: float = Field(default=0.0, ge=0, description="Weight of the task (kg)")
    status: str = Field(default="unassigned", description="Status of the task") # e.g., 'unassigned', 'assigned', 'completed'


class TaskCreate(TaskBase):
    # Create Task model
    pass


class TaskUpdate(BaseModel):
    # Update Task model
    pickup_location: Optional[Tuple[float, float]] = Field(None, description="Pickup location (lat, lon)")  
    dropoff_location: Optional[Tuple[float, float]] = Field(None, description="Dropoff location (lat, lon)")  
    weight: Optional[float] = Field(None, ge=0, description="Weight of the task (kg)")
    status: Optional[str] = Field(None, description="Status of the task")  # e.g., 'unassigned', 'assigned', 'completed'

class TaskResponse(TaskBase):
    # API Response model (including ID)
    id: int
    class Config:
        from_attributes = True
