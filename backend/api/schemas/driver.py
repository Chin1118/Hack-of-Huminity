from typing import Literal, Optional

from pydantic import BaseModel, Field

VehicleType = Literal["fuel", "electric", "hybrid"]


class DriverBase(BaseModel):
    start_location: list[float] = Field(
        ...,
        min_length=2,
        max_length=2,
        description="Start location [lng, lat]",
    )
    vehicle_type: VehicleType = Field(default="fuel")
    capacity: float = Field(default=0.0, ge=0, description="Capacity (kg)")
    available: bool = Field(default=True, description="Availability")


class DriverUpdate(BaseModel):
    start_location: Optional[list[float]] = Field(default=None, min_length=2, max_length=2)
    vehicle_type: Optional[VehicleType] = None
    capacity: Optional[float] = Field(default=None, ge=0)
    available: Optional[bool] = None


class DriverResponse(DriverBase):
    id: str
