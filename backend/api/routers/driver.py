from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from backend.api.schemas.driver import DriverResponse, DriverUpdate
from backend.core.authz.authorization_guard import ensure_admin
from backend.core.authz.dependencies import RequestUser, get_current_user
from backend.core.errors.error_contract import api_error
from backend.utils.supabase_client import supabase

router = APIRouter(prefix="/drivers", tags=["drivers"])


def _coerce_driver_row(row: dict[str, Any]) -> DriverResponse:
    start_location = row.get("start_location")
    if not isinstance(start_location, list) or len(start_location) != 2:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Invalid driver start_location format in database.",
        )
    return DriverResponse(
        id=str(row.get("id", "")),
        start_location=[float(start_location[0]), float(start_location[1])],
        vehicle_type=row.get("vehicle_type", "fuel"),
        capacity=float(row.get("capacity", 0.0)),
        available=bool(row.get("available", True)),
    )


@router.get("/", response_model=list[DriverResponse])
def get_all_drivers(current_user: RequestUser = Depends(get_current_user)):
    ensure_admin(current_user, detail="Only admin can read all drivers.")

    try:
        response = supabase.table("drivers").select("*").execute()
        rows = getattr(response, "data", None) or []
        return [_coerce_driver_row(row) for row in rows]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=api_error(
                "drivers_read_failed",
                f"Failed to read drivers from Supabase: {e}",
                category="upstream",
                retryable=True,
            ),
        ) from e


@router.get("/me", response_model=DriverResponse)
def get_my_driver(current_user: RequestUser = Depends(get_current_user)):
    try:
        response = (
            supabase.table("drivers")
            .select("*")
            .eq("id", current_user.user_id)
            .limit(1)
            .execute()
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=api_error(
                "driver_me_read_failed",
                f"Failed to read current driver from Supabase: {e}",
                category="upstream",
                retryable=True,
            ),
        ) from e
    rows = getattr(response, "data", None) or []
    if not rows:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=api_error(
                "driver_not_found",
                "Driver profile not found for current user.",
                category="business",
            ),
        )
    return _coerce_driver_row(rows[0])


@router.patch("/me", response_model=DriverResponse)
def update_my_driver(
    payload: DriverUpdate,
    current_user: RequestUser = Depends(get_current_user),
):
    update_data = payload.model_dump(exclude_unset=True, exclude_none=True)
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=api_error(
                "driver_update_empty",
                "No fields provided for update.",
                category="validation",
            ),
        )

    try:
        supabase.table("drivers").update(update_data).eq("id", current_user.user_id).execute()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=api_error(
                "driver_me_update_failed",
                f"Failed to update current driver in Supabase: {e}",
                category="upstream",
                retryable=True,
            ),
        ) from e
    try:
        response = (
            supabase.table("drivers")
            .select("*")
            .eq("id", current_user.user_id)
            .limit(1)
            .execute()
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=api_error(
                "driver_me_read_after_update_failed",
                f"Failed to read current driver after update: {e}",
                category="upstream",
                retryable=True,
            ),
        ) from e

    rows = getattr(response, "data", None) or []
    if not rows:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=api_error(
                "driver_not_found",
                "Driver profile not found for current user.",
                category="business",
            ),
        )

    return _coerce_driver_row(rows[0])
