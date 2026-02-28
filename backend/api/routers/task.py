import math
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from backend.api.schemas.task import (
    DriverTaskAssignments,
    PendingTasksCountResponse,
    TaskAssignmentItem,
    TaskArriveRequest,
    TaskCreate,
    TaskIdsResponse,
    TaskResponse,
    TaskUpdate,
    TodayAssignmentsResponse,
)
from backend.core.authz.authorization_guard import ensure_admin, ensure_self_or_admin
from backend.core.authz.dependencies import RequestUser, get_current_user
from backend.core.errors.error_contract import api_error
from backend.utils.supabase_client import supabase

router = APIRouter(prefix="/tasks", tags=["tasks"])


def _extract_task_name(note: Any, task_id: str) -> str:
    fallback = f"Task {task_id[:8]}"
    if note is None:
        return fallback
    text = str(note).strip()
    if not text:
        return fallback
    first_line = text.splitlines()[0].strip()
    if first_line.lower().startswith("task:"):
        parsed = first_line.split(":", 1)[1].strip()
        return parsed or fallback
    return first_line[:80]


def _display_driver_name(row: dict[str, Any], driver_id: str) -> str:
    for key in ("name", "display_name", "full_name", "username", "email"):
        value = row.get(key)
        if value is not None and str(value).strip():
            return str(value).strip()
    return f"Driver {driver_id[:8]}"


def _is_status_not_null_error(exc: Exception) -> bool:
    message = str(exc).lower()
    return (
        "null value in column" in message
        and "status" in message
        and "not-null" in message
    )


def _coerce_task_row(row: dict[str, Any]) -> TaskResponse:
    pickup = row.get("pickup_location")
    dropoff = row.get("dropoff_location")
    if not isinstance(pickup, list) or len(pickup) != 2:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Invalid pickup_location format in database.",
        )
    if not isinstance(dropoff, list) or len(dropoff) != 2:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Invalid dropoff_location format in database.",
        )
    return TaskResponse(
        id=str(row.get("id", "")),
        driver_id=row.get("driver_id"),
        pickup_location=[float(pickup[0]), float(pickup[1])],
        dropoff_location=[float(dropoff[0]), float(dropoff[1])],
        note=row.get("note"),
        type=row.get("type"),
        status=row.get("status"),
        created_at=row.get("created_at"),
        updated_at=row.get("updated_at"),
    )


def _haversine_distance_m(
    start_lng: float,
    start_lat: float,
    end_lng: float,
    end_lat: float,
) -> float:
    earth_radius_m = 6371000.0
    d_lat = math.radians(end_lat - start_lat)
    d_lng = math.radians(end_lng - start_lng)
    a = (
        math.sin(d_lat / 2) ** 2
        + math.cos(math.radians(start_lat))
        * math.cos(math.radians(end_lat))
        * math.sin(d_lng / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return earth_radius_m * c


@router.get("/me", response_model=list[TaskResponse])
def get_my_tasks(current_user: RequestUser = Depends(get_current_user)):
    try:
        response = (
            supabase.table("tasks")
            .select("*")
            .eq("driver_id", current_user.user_id)
            .execute()
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=api_error(
                "tasks_read_failed",
                f"Failed to read tasks from Supabase: {e}",
                category="upstream",
                retryable=True,
            ),
        ) from e

    rows = getattr(response, "data", None) or []
    return [_coerce_task_row(row) for row in rows]


@router.get("/me/ids", response_model=TaskIdsResponse)
def get_my_task_ids(current_user: RequestUser = Depends(get_current_user)):
    try:
        response = (
            supabase.table("tasks")
            .select("id")
            .eq("driver_id", current_user.user_id)
            .execute()
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=api_error(
                "task_ids_read_failed",
                f"Failed to read task ids from Supabase: {e}",
                category="upstream",
                retryable=True,
            ),
        ) from e

    rows = getattr(response, "data", None) or []
    return TaskIdsResponse(task_ids=[str(row.get("id", "")) for row in rows])


@router.get("/admin/today-assignments", response_model=TodayAssignmentsResponse)
def get_today_assignments(current_user: RequestUser = Depends(get_current_user)):
    ensure_admin(current_user, detail="Only admin can read today's assignments.")

    now_utc = datetime.now(timezone.utc)
    day_start = datetime(
        now_utc.year,
        now_utc.month,
        now_utc.day,
        tzinfo=timezone.utc,
    )
    terminal_statuses = {"completed", "done", "closed", "cancelled", "canceled"}

    try:
        response = (
            supabase.table("tasks")
            .select("id,driver_id,created_at,note,status")
            .not_.is_("driver_id", "null")
            .order("created_at", desc=False)
            .execute()
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=api_error(
                "today_assignments_read_failed",
                f"Failed to read today's assignments from Supabase: {e}",
                category="upstream",
                retryable=True,
            ),
        ) from e

    rows = getattr(response, "data", None) or []
    grouped: dict[str, list[TaskAssignmentItem]] = {}
    for row in rows:
        status_raw = row.get("status")
        status_normalized = str(status_raw).strip().lower() if status_raw is not None else ""
        if status_normalized in terminal_statuses:
            continue
        driver_id = str(row.get("driver_id", "")).strip()
        task_id = str(row.get("id", "")).strip()
        if not driver_id or not task_id:
            continue
        task_name = _extract_task_name(row.get("note"), task_id)
        grouped.setdefault(driver_id, []).append(
            TaskAssignmentItem(task_id=task_id, task_name=task_name)
        )

    driver_names: dict[str, str] = {}
    driver_ids = sorted(grouped.keys())
    if driver_ids:
        try:
            profile_resp = (
                supabase.table("profile")
                .select("*")
                .in_("id", driver_ids)
                .execute()
            )
            profile_rows = getattr(profile_resp, "data", None) or []
            for row in profile_rows:
                driver_id = str(row.get("id", "")).strip()
                if not driver_id:
                    continue
                driver_names[driver_id] = _display_driver_name(row, driver_id)
        except Exception:
            driver_names = {}

    assignments = [
        DriverTaskAssignments(
            driver_id=driver_id,
            driver_name=driver_names.get(driver_id, f"Driver {driver_id[:8]}"),
            tasks=tasks,
        )
        for driver_id, tasks in sorted(grouped.items(), key=lambda item: item[0])
    ]
    return TodayAssignmentsResponse(
        date_utc=day_start.date().isoformat(),
        total_assigned_tasks=sum(len(item.tasks) for item in assignments),
        assignments=assignments,
    )


@router.get("/admin/pending-count", response_model=PendingTasksCountResponse)
def get_pending_tasks_count(current_user: RequestUser = Depends(get_current_user)):
    ensure_admin(current_user, detail="Only admin can read pending task count.")

    terminal_statuses = {"completed", "done", "closed", "cancelled", "canceled"}
    try:
        response = (
            supabase.table("tasks")
            .select("id,status")
            .is_("driver_id", "null")
            .execute()
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=api_error(
                "pending_tasks_read_failed",
                f"Failed to read pending tasks from Supabase: {e}",
                category="upstream",
                retryable=True,
            ),
        ) from e

    rows = getattr(response, "data", None) or []
    pending_count = 0
    for row in rows:
        status_raw = row.get("status")
        status_normalized = str(status_raw).strip().lower() if status_raw is not None else ""
        if status_normalized in terminal_statuses:
            continue
        pending_count += 1

    return PendingTasksCountResponse(pending_tasks=pending_count)


@router.get("/admin/assigned-active", response_model=list[TaskResponse])
def get_admin_assigned_active_tasks(current_user: RequestUser = Depends(get_current_user)):
    ensure_admin(current_user, detail="Only admin can read assigned active tasks.")

    terminal_statuses = {"completed", "done", "closed", "cancelled", "canceled"}
    try:
        response = (
            supabase.table("tasks")
            .select("*")
            .not_.is_("driver_id", "null")
            .execute()
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=api_error(
                "assigned_tasks_read_failed",
                f"Failed to read assigned tasks from Supabase: {e}",
                category="upstream",
                retryable=True,
            ),
        ) from e

    rows = getattr(response, "data", None) or []
    filtered_rows: list[dict[str, Any]] = []
    for row in rows:
        status_raw = row.get("status")
        status_normalized = str(status_raw).strip().lower() if status_raw is not None else ""
        if status_normalized in terminal_statuses:
            continue
        filtered_rows.append(row)
    return [_coerce_task_row(row) for row in filtered_rows]


@router.get("/{task_id}", response_model=TaskResponse)
def get_task(task_id: str, current_user: RequestUser = Depends(get_current_user)):
    try:
        query = supabase.table("tasks").select("*").eq("id", task_id)
        if current_user.role != "admin":
            query = query.eq("driver_id", current_user.user_id)
        response = query.limit(1).execute()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=api_error(
                "task_read_failed",
                f"Failed to read task from Supabase: {e}",
                category="upstream",
                retryable=True,
            ),
        ) from e

    rows = getattr(response, "data", None) or []
    if not rows:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=api_error(
                "task_not_found",
                f"Task {task_id} not found.",
                category="business",
            ),
        )
    return _coerce_task_row(rows[0])


@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(payload: TaskCreate, current_user: RequestUser = Depends(get_current_user)):
    requested_driver_id = (payload.driver_id or "").strip()
    if requested_driver_id:
        target_driver_id = requested_driver_id
    elif current_user.role == "admin":
        target_driver_id = None
    else:
        target_driver_id = current_user.user_id

    if target_driver_id is not None:
        ensure_self_or_admin(
            current_user,
            target_driver_id,
            detail="Drivers can only create tasks assigned to themselves.",
        )

    insert_data = {
        "driver_id": target_driver_id,
        "pickup_location": payload.pickup_location,
        "dropoff_location": payload.dropoff_location,
        "note": payload.note,
        "type": payload.type or "parcel",
        "status": payload.status or "available",
    }
    try:
        response = supabase.table("tasks").insert(insert_data).execute()
    except Exception as e:
        # Backward compatibility for schemas where `status` is NOT NULL
        # and has no DB default value.
        if _is_status_not_null_error(e):
            insert_data_with_status = {**insert_data, "status": "available"}
            try:
                response = (
                    supabase.table("tasks").insert(insert_data_with_status).execute()
                )
            except Exception as inner:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=api_error(
                        "task_create_failed",
                        f"Failed to create task in Supabase: {inner}",
                        category="upstream",
                        retryable=True,
                    ),
                ) from inner
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=api_error(
                    "task_create_failed",
                    f"Failed to create task in Supabase: {e}",
                    category="upstream",
                    retryable=True,
                ),
            ) from e

    rows = getattr(response, "data", None) or []
    if not rows:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=api_error(
                "task_create_empty",
                "Task creation returned empty response.",
                category="upstream",
                retryable=True,
            ),
        )
    return _coerce_task_row(rows[0])


@router.patch("/{task_id}", response_model=TaskResponse)
def update_task(
    task_id: str,
    payload: TaskUpdate,
    current_user: RequestUser = Depends(get_current_user),
):
    update_data = payload.model_dump(exclude_unset=True, exclude_none=True)
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=api_error(
                "task_update_empty",
                "No fields provided for update.",
                category="validation",
            ),
        )

    try:
        query = supabase.table("tasks").update(update_data).eq("id", task_id)
        if current_user.role != "admin":
            query = query.eq("driver_id", current_user.user_id)
        response = query.execute()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=api_error(
                "task_update_failed",
                f"Failed to update task in Supabase: {e}",
                category="upstream",
                retryable=True,
            ),
        ) from e

    rows = getattr(response, "data", None) or []
    if not rows:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=api_error(
                "task_not_found",
                f"Task {task_id} not found.",
                category="business",
            ),
        )
    return _coerce_task_row(rows[0])


@router.post("/{task_id}/arrive", response_model=TaskResponse)
def arrive_task(
    task_id: str,
    payload: TaskArriveRequest,
    current_user: RequestUser = Depends(get_current_user),
):
    try:
        query = supabase.table("tasks").select("*").eq("id", task_id)
        if current_user.role != "admin":
            query = query.eq("driver_id", current_user.user_id)
        read_response = query.limit(1).execute()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=api_error(
                "task_read_failed",
                f"Failed to read task from Supabase: {e}",
                category="upstream",
                retryable=True,
            ),
        ) from e

    rows = getattr(read_response, "data", None) or []
    if not rows:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=api_error(
                "task_not_found",
                f"Task {task_id} not found.",
                category="business",
            ),
        )

    row = rows[0]
    dropoff = row.get("dropoff_location")
    if not isinstance(dropoff, list) or len(dropoff) != 2:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=api_error(
                "task_dropoff_invalid",
                "Task dropoff_location is invalid.",
                category="upstream",
            ),
        )

    current_lng = float(payload.current_location[0])
    current_lat = float(payload.current_location[1])
    dropoff_lng = float(dropoff[0])
    dropoff_lat = float(dropoff[1])
    distance_m = _haversine_distance_m(
        current_lng,
        current_lat,
        dropoff_lng,
        dropoff_lat,
    )
    within_range = distance_m <= float(payload.radius_m)
    if not within_range:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=api_error(
                "task_not_near_dropoff",
                "Driver is not near the dropoff location yet.",
                category="business",
                context={
                    "distance_m": round(distance_m, 2),
                    "radius_m": float(payload.radius_m),
                    "task_id": task_id,
                },
            ),
        )

    try:
        update_query = supabase.table("tasks").update({"status": "completed"}).eq("id", task_id)
        if current_user.role != "admin":
            update_query = update_query.eq("driver_id", current_user.user_id)
        update_response = update_query.execute()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=api_error(
                "task_arrive_update_failed",
                f"Failed to mark task as completed: {e}",
                category="upstream",
                retryable=True,
            ),
        ) from e

    updated_rows = getattr(update_response, "data", None) or []
    if not updated_rows:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=api_error(
                "task_not_found",
                f"Task {task_id} not found.",
                category="business",
            ),
        )
    return _coerce_task_row(updated_rows[0])
