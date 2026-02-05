from pydantic import BaseModel, Field
from typing import Tuple, Optional


class DriverBase(BaseModel):
    start_location: Tuple[float, float] = Field(..., description="Start location (x, y)")
    vehicle_type: str = Field(..., description="Vehicle type: 'fuel' or 'ev'")
    capacity: float = Field(default=0.0, ge=0, description="Capacity (kg)")
    available: bool = Field(default=True, description="Available")


class DriverCreate(DriverBase):
    # Create Driver model
    pass


class DriverUpdate(BaseModel):
    # Update Driver model
    start_location: Optional[Tuple[float, float]] = None
    vehicle_type: Optional[str] = None
    capacity: Optional[float] = Field(default=None, ge=0)
    available: Optional[bool] = None


class DriverResponse(DriverBase):
    # API Response model (including ID)
    id: int
    class Config:
        from_attributes = True
