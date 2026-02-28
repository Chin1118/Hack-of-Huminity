from collections import defaultdict
from dataclasses import dataclass
from typing import Any
import math

from fastapi import APIRouter, Depends, HTTPException, status

from backend.api.schemas.aco_optimizer import (
    DispatchAllRequest,
    DispatchAllResponse,
    DriverTaskAssignment,
    RouteVisualizationItem,
    RouteVisualizationResponse,
    SolveRequest,
    SolveResponse,
)
from backend.core.authz.authorization_guard import ensure_admin, ensure_self_or_admin
from backend.core.authz.dependencies import RequestUser, get_current_user
from backend.core.errors.error_contract import api_error
from backend.features.route_optimization.aco_optimizer import (
    ACOOptimizer,
    run_multi_driver_aco,
)
from backend.features.route_optimization.network_mode_selector import (
    can_fallback_to_euclidean,
    choose_preferred_mode,
)
from backend.features.task_assignment.task_dispatcher import TaskDispatcher
from backend.models.emission import EmissionModel
from backend.models.pheromone import load_pheromone_matrix
from backend.models.task import Task
from backend.utils.road_network import RoadNetwork
from backend.utils.supabase_client import supabase

router = APIRouter(prefix="/optimization", tags=["optimization"])
_ADMIN_ROUTE_PALETTE = [
    "#FF3B30",
    "#34C759",
    "#FF9500",
    "#AF52DE",
    "#30B0C7",
    "#5856D6",
]
_DRIVER_IOS_BLUE = "#007AFF"
_LATEST_BEST_PATH_NODES_BY_DRIVER: dict[str, list[str]] = {}


@dataclass
class OptimizerDriver:
    id: str
    start_location: tuple[float, float]
    vehicle_type: str
    capacity: float
    available: bool
    emission_model: EmissionModel


def _coerce_driver(row: dict[str, Any]) -> OptimizerDriver:
    start = row.get("start_location")
    if not isinstance(start, list) or len(start) != 2:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Invalid driver start_location format in database.",
        )
    return OptimizerDriver(
        id=str(row.get("id", "")),
        start_location=(float(start[0]), float(start[1])),
        vehicle_type=str(row.get("vehicle_type", "fuel")),
        capacity=float(row.get("capacity", 0.0)),
        available=bool(row.get("available", True)),
        emission_model=EmissionModel(),
    )


def _coerce_task(row: dict[str, Any]) -> Task:
    pickup = row.get("pickup_location")
    dropoff = row.get("dropoff_location")
    if not isinstance(pickup, list) or len(pickup) != 2:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Invalid task pickup_location format in database.",
        )
    if not isinstance(dropoff, list) or len(dropoff) != 2:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Invalid task dropoff_location format in database.",
        )
    return Task(
        id=str(row.get("id", "")),
        pickup_location=(float(pickup[0]), float(pickup[1])),
        dropoff_location=(float(dropoff[0]), float(dropoff[1])),
    )


def _distance(a: tuple[float, float], b: tuple[float, float]) -> float:
    return math.dist(a, b)


def _resolve_unique_assignments(
    scored_assignments: list[dict[str, float | str]],
    tasks: list[Task],
    drivers: list[OptimizerDriver],
) -> tuple[dict[str, str], int]:
    by_task: dict[str, list[dict[str, float | str]]] = defaultdict(list)
    for score in scored_assignments:
        by_task[str(score["task_id"])].append(score)

    final_assignments: dict[str, str] = {}
    conflict_resolved_count = 0

    for task_id, candidates in by_task.items():
        ranked = sorted(
            candidates,
            key=lambda item: (float(item["total_cost"]), str(item["driver_id"])),
        )
        winner = ranked[0]
        final_assignments[task_id] = str(winner["driver_id"])
        if len(ranked) > 1:
            conflict_resolved_count += len(ranked) - 1

    for task in tasks:
        task_id = str(task.id)
        if task_id in final_assignments:
            continue
        if not drivers:
            continue
        nearest = min(
            drivers,
            key=lambda driver: _distance(driver.start_location, task.pickup_location),
        )
        final_assignments[task_id] = str(nearest.id)

    return final_assignments, conflict_resolved_count


def _persist_assignments(assignments: dict[str, str]) -> None:
    for task_id, driver_id in assignments.items():
        try:
            supabase.table("tasks").update({"driver_id": driver_id}).eq("id", task_id).execute()
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=api_error(
                    "optimizer_assignment_update_failed",
                    f"Failed to update task assignment in Supabase: {e}",
                    category="upstream",
                    retryable=True,
                    context={"task_id": task_id, "driver_id": driver_id},
                ),
            ) from e


def _build_driver_assignments(assignments: dict[str, str]) -> list[DriverTaskAssignment]:
    grouped: dict[str, list[str]] = defaultdict(list)
    for task_id, driver_id in assignments.items():
        grouped[str(driver_id)].append(str(task_id))
    return [
        DriverTaskAssignment(driver_id=driver_id, task_ids=sorted(task_ids))
        for driver_id, task_ids in sorted(grouped.items(), key=lambda item: item[0])
    ]


def _load_dispatch_tasks_from_supabase() -> list[Task]:
    """
    Load tasks that still need assignment.
    Rules:
    - `driver_id` must be NULL (unassigned)
    - `status` can be NULL/empty/available/accepted/in_progress
    - exclude terminal statuses like completed/done/closed
    """
    task_resp = supabase.table("tasks").select("*").is_("driver_id", "null").execute()
    rows = getattr(task_resp, "data", None) or []

    terminal_statuses = {"completed", "done", "closed", "cancelled", "canceled"}

    filtered_rows: list[dict[str, Any]] = []
    for row in rows:
        status_raw = row.get("status")
        status_normalized = str(status_raw).strip().lower() if status_raw is not None else ""
        if status_normalized in terminal_statuses:
            continue
        filtered_rows.append(row)

    return [_coerce_task(row) for row in filtered_rows]


def _task_id_from_node(node_id: str) -> str | None:
    if not node_id.startswith("T_"):
        return None
    if node_id.endswith("_D"):
        return node_id[2:-2]
    return node_id[2:]


def _color_for_driver(driver_id: str) -> str:
    index = sum(driver_id.encode("utf-8")) % len(_ADMIN_ROUTE_PALETTE)
    return _ADMIN_ROUTE_PALETTE[index]


def _filter_nodes_to_assigned(
    nodes: list[str],
    assigned_task_ids: set[str],
    driver_id: str,
) -> list[str]:
    filtered = [f"D_{driver_id}"]
    for node_id in nodes:
        task_id = _task_id_from_node(node_id)
        if task_id is None:
            continue
        if task_id in assigned_task_ids:
            filtered.append(node_id)
    return filtered


def _build_route_geometry_for_driver(
    driver: OptimizerDriver,
    all_tasks_by_id: dict[str, Task],
    best_path_nodes: list[str],
    mode: str,
) -> tuple[dict[str, Any], float, float, dict[str, Any] | None]:
    task_ids = {
        task_id for task_id in (_task_id_from_node(node) for node in best_path_nodes) if task_id
    }
    route_tasks = [all_tasks_by_id[task_id] for task_id in task_ids if task_id in all_tasks_by_id]
    if len(best_path_nodes) < 2:
        return ({"type": "LineString", "coordinates": []}, 0.0, 0.0, None)

    network = RoadNetwork(
        drivers=[driver],
        tasks=route_tasks,
        mode=mode,
        # Visualization only needs Directions geometry; skip Matrix prewarm to avoid
        # failing on large route node counts (>25).
        warm_up_matrix=False,
    )
    route_response = network.get_tour_route(best_path_nodes, include_steps=True)
    if not route_response:
        return ({"type": "LineString", "coordinates": []}, 0.0, 0.0, None)

    routes = route_response.get("routes") or []
    if not routes:
        return ({"type": "LineString", "coordinates": []}, 0.0, 0.0, None)

    primary = routes[0]
    geometry = primary.get("geometry") or {"type": "LineString", "coordinates": []}
    distance_m = float(primary.get("distance") or 0.0)
    duration_s = float(primary.get("duration") or 0.0)
    navigation = _extract_next_navigation(primary)
    return (geometry, distance_m, duration_s, navigation)


def _extract_next_navigation(primary_route: dict[str, Any]) -> dict[str, Any] | None:
    legs = primary_route.get("legs") or []
    if not legs:
        return None
    steps = (legs[0] or {}).get("steps") or []
    if not steps:
        return None
    step = steps[0] or {}
    maneuver = step.get("maneuver") or {}

    instruction = maneuver.get("instruction")
    road_name = step.get("name")
    distance_m = step.get("distance")
    modifier = maneuver.get("modifier")
    speed_limit_kmh = _extract_speed_limit_kmh(step=step, leg=legs[0] or {})

    if not instruction and road_name:
        instruction = f"Continue on {road_name}"

    return {
        "instruction": str(instruction) if instruction else None,
        "road_name": str(road_name) if road_name else None,
        "distance_m": float(distance_m) if distance_m is not None else None,
        "maneuver_modifier": str(modifier) if modifier else None,
        "speed_limit_kmh": speed_limit_kmh,
    }


def _extract_speed_limit_kmh(step: dict[str, Any], leg: dict[str, Any]) -> float | None:
    direct_candidates = (
        step.get("speed_limit"),
        step.get("speedLimit"),
        (step.get("driving_side") or {}).get("speed_limit")
        if isinstance(step.get("driving_side"), dict)
        else None,
    )
    for value in direct_candidates:
        parsed = _to_kmh(value)
        if parsed is not None:
            return parsed

    annotation = leg.get("annotation") or {}
    if not isinstance(annotation, dict):
        return None
    maxspeed = annotation.get("maxspeed")
    if not isinstance(maxspeed, list) or not maxspeed:
        return None

    for item in maxspeed:
        parsed = _to_kmh(item)
        if parsed is not None:
            return parsed
    return None


def _to_kmh(value: Any) -> float | None:
    if value is None:
        return None

    if isinstance(value, (int, float)):
        numeric = float(value)
        if numeric <= 0:
            return None
        # Most APIs already return km/h; keep as-is.
        return numeric

    if isinstance(value, str):
        text = value.strip().lower()
        if not text or text == "none" or text == "unknown":
            return None
        if text.endswith("mph"):
            try:
                mph = float(text.replace("mph", "").strip())
            except ValueError:
                return None
            if mph <= 0:
                return None
            return mph * 1.60934
        try:
            parsed = float(text)
            return parsed if parsed > 0 else None
        except ValueError:
            return None

    if isinstance(value, dict):
        speed = value.get("speed")
        unit = str(value.get("unit") or "").strip().lower()
        if speed is None:
            return None
        try:
            numeric_speed = float(speed)
        except (TypeError, ValueError):
            return None
        if numeric_speed <= 0:
            return None
        if unit == "mph":
            return numeric_speed * 1.60934
        return numeric_speed

    return None


def _extract_pickup_dropoff_points(
    best_path_nodes: list[str],
    all_tasks_by_id: dict[str, Task],
) -> tuple[list[list[float]], list[list[float]]]:
    pickup_points: list[list[float]] = []
    dropoff_points: list[list[float]] = []
    for node_id in best_path_nodes:
        task_id = _task_id_from_node(node_id)
        if task_id is None:
            continue
        task = all_tasks_by_id.get(task_id)
        if task is None:
            continue
        if node_id.endswith("_D"):
            dropoff_points.append([float(task.dropoff_location[0]), float(task.dropoff_location[1])])
        else:
            pickup_points.append([float(task.pickup_location[0]), float(task.pickup_location[1])])
    return pickup_points, dropoff_points


def _load_non_terminal_tasks_for_driver(driver_id: str) -> list[Task]:
    terminal_statuses = {"completed", "done", "closed", "cancelled", "canceled"}
    task_resp = (
        supabase.table("tasks")
        .select("*")
        .eq("driver_id", driver_id)
        .execute()
    )
    rows = getattr(task_resp, "data", None) or []
    filtered_rows: list[dict[str, Any]] = []
    for row in rows:
        status_raw = row.get("status")
        status_normalized = str(status_raw).strip().lower() if status_raw is not None else ""
        if status_normalized in terminal_statuses:
            continue
        filtered_rows.append(row)
    return [_coerce_task(row) for row in filtered_rows]


def _ensure_best_path_cached(driver: OptimizerDriver) -> list[str]:
    driver_id = str(driver.id)
    cached = _LATEST_BEST_PATH_NODES_BY_DRIVER.get(driver_id, [])
    if cached:
        return cached

    try:
        tasks = _load_non_terminal_tasks_for_driver(driver_id)
    except Exception:
        return []

    if not tasks:
        return []

    preferred_mode = choose_preferred_mode()
    pheromone_matrix = load_pheromone_matrix()
    try:
        optimizer = ACOOptimizer(
            driver=driver,
            tasks=tasks,
            road_mode=preferred_mode,
            pheromone_matrix=pheromone_matrix,
        )
        result = optimizer.solve()
    except Exception:
        if can_fallback_to_euclidean(preferred_mode):
            optimizer = ACOOptimizer(
                driver=driver,
                tasks=tasks,
                road_mode="euclidean",
                pheromone_matrix=pheromone_matrix,
            )
            result = optimizer.solve()
        else:
            return []

    best_path_nodes = list(result.get("best_path_nodes", []))
    _LATEST_BEST_PATH_NODES_BY_DRIVER[driver_id] = best_path_nodes
    return best_path_nodes


@router.post("/solve", response_model=SolveResponse)
def solve(req: SolveRequest, current_user: RequestUser = Depends(get_current_user)):
    target_driver_id = req.driver_id or current_user.user_id
    ensure_self_or_admin(
        current_user,
        target_driver_id,
        detail="Drivers can only run optimization for themselves.",
    )

    try:
        driver_resp = (
            supabase.table("drivers")
            .select("*")
            .eq("id", target_driver_id)
            .limit(1)
            .execute()
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=api_error(
                "optimizer_driver_read_failed",
                f"Failed to load driver from Supabase: {e}",
                category="upstream",
                retryable=True,
            ),
        ) from e

    driver_rows = getattr(driver_resp, "data", None) or []
    if not driver_rows:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=api_error("driver_not_found", "Driver not found.", category="business"),
        )
    driver = _coerce_driver(driver_rows[0])

    try:
        task_resp = (
            supabase.table("tasks")
            .select("*")
            .eq("driver_id", target_driver_id)
            .execute()
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=api_error(
                "optimizer_tasks_read_failed",
                f"Failed to load tasks from Supabase: {e}",
                category="upstream",
                retryable=True,
            ),
        ) from e

    task_rows = getattr(task_resp, "data", None) or []
    tasks = [_coerce_task(row) for row in task_rows]

    preferred_mode = choose_preferred_mode()
    mode_used = preferred_mode
    pheromone_matrix = load_pheromone_matrix()
    try:
        optimizer = ACOOptimizer(
            driver=driver,
            tasks=tasks,
            road_mode=preferred_mode,
            pheromone_matrix=pheromone_matrix,
        )
        result = optimizer.solve()
    except Exception as e:
        if can_fallback_to_euclidean(preferred_mode):
            mode_used = "euclidean"
            optimizer = ACOOptimizer(
                driver=driver,
                tasks=tasks,
                road_mode="euclidean",
                pheromone_matrix=pheromone_matrix,
            )
            result = optimizer.solve()
        else:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=api_error(
                    "optimizer_unavailable",
                    f"Optimization unavailable in mode={preferred_mode}: {e}",
                    category="upstream",
                    retryable=True,
                    context={"mode": preferred_mode},
                ),
            ) from e

    best_path_nodes = result.get("best_path_nodes", [])
    _LATEST_BEST_PATH_NODES_BY_DRIVER[str(target_driver_id)] = list(best_path_nodes)
    return SolveResponse(
        driver_id=str(result.get("driver_id", target_driver_id)),
        best_path_nodes=best_path_nodes,
        metrics=result.get("metrics", {}),
        mode_used=mode_used,
    )


@router.post("/dispatch-all", response_model=DispatchAllResponse)
def dispatch_all(
    req: DispatchAllRequest,
    current_user: RequestUser = Depends(get_current_user),
):
    ensure_admin(current_user, detail="Only admins can dispatch tasks to all drivers.")

    try:
        driver_resp = supabase.table("drivers").select("*").eq("available", True).execute()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=api_error(
                "optimizer_driver_read_failed",
                f"Failed to load drivers from Supabase: {e}",
                category="upstream",
                retryable=True,
            ),
        ) from e

    drivers = [_coerce_driver(row) for row in (getattr(driver_resp, "data", None) or [])]
    if not drivers:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=api_error(
                "optimizer_no_available_drivers",
                "No available drivers found.",
                category="business",
            ),
        )

    try:
        tasks = _load_dispatch_tasks_from_supabase()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=api_error(
                "optimizer_tasks_read_failed",
                f"Failed to load dispatch tasks from Supabase: {e}",
                category="upstream",
                retryable=True,
            ),
        ) from e
    if not tasks:
        return DispatchAllResponse(
            mode_used="none",
            assigned_count=0,
            unassigned_count=0,
            conflict_resolved_count=0,
            driver_assignments=[],
        )

    dispatcher = TaskDispatcher(drivers=drivers)
    candidate_map = dispatcher.build_available_task_candidates(
        tasks=tasks,
        top_k=req.top_k_candidates,
    )

    preferred_mode = choose_preferred_mode()
    mode_used = preferred_mode
    pheromone_matrix = load_pheromone_matrix()
    try:
        optimization = run_multi_driver_aco(
            drivers=drivers,
            tasks=tasks,
            candidate_map=candidate_map,
            road_mode=preferred_mode,
            pheromone_matrix=pheromone_matrix,
        )
    except Exception as e:
        if can_fallback_to_euclidean(preferred_mode):
            mode_used = "euclidean"
            optimization = run_multi_driver_aco(
                drivers=drivers,
                tasks=tasks,
                candidate_map=candidate_map,
                road_mode="euclidean",
                pheromone_matrix=pheromone_matrix,
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=api_error(
                    "optimizer_unavailable",
                    f"Dispatch optimization unavailable in mode={preferred_mode}: {e}",
                    category="upstream",
                    retryable=True,
                    context={"mode": preferred_mode},
                ),
            ) from e

    scored_assignments = optimization.get("scored_assignments", [])
    final_assignments, conflict_resolved_count = _resolve_unique_assignments(
        scored_assignments=scored_assignments,
        tasks=tasks,
        drivers=drivers,
    )
    _persist_assignments(final_assignments)
    driver_to_assigned_tasks: dict[str, set[str]] = defaultdict(set)
    for task_id, driver_id in final_assignments.items():
        driver_to_assigned_tasks[str(driver_id)].add(str(task_id))

    per_driver_results = optimization.get("per_driver_results", {})
    for driver in drivers:
        driver_id = str(driver.id)
        raw_nodes = list(
            (per_driver_results.get(driver_id, {}) or {}).get("best_path_nodes", [])
        )
        filtered_nodes = _filter_nodes_to_assigned(
            nodes=raw_nodes,
            assigned_task_ids=driver_to_assigned_tasks.get(driver_id, set()),
            driver_id=driver_id,
        )
        _LATEST_BEST_PATH_NODES_BY_DRIVER[driver_id] = filtered_nodes

    assigned_count = len(final_assignments)
    unassigned_count = max(0, len(tasks) - assigned_count)
    return DispatchAllResponse(
        mode_used=mode_used,
        assigned_count=assigned_count,
        unassigned_count=unassigned_count,
        conflict_resolved_count=conflict_resolved_count,
        driver_assignments=_build_driver_assignments(final_assignments),
    )


@router.get("/routes/visualization", response_model=RouteVisualizationResponse)
def get_route_visualization(current_user: RequestUser = Depends(get_current_user)):
    try:
        driver_resp = supabase.table("drivers").select("*").execute()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=api_error(
                "optimizer_driver_read_failed",
                f"Failed to load drivers from Supabase: {e}",
                category="upstream",
                retryable=True,
            ),
        ) from e

    all_drivers = [_coerce_driver(row) for row in (getattr(driver_resp, "data", None) or [])]
    if current_user.role == "admin":
        target_drivers = all_drivers
        view_mode = "admin"
    else:
        target_drivers = [driver for driver in all_drivers if str(driver.id) == current_user.user_id]
        view_mode = "driver"

    try:
        task_resp = supabase.table("tasks").select("*").execute()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=api_error(
                "optimizer_tasks_read_failed",
                f"Failed to load tasks from Supabase: {e}",
                category="upstream",
                retryable=True,
            ),
        ) from e
    all_tasks_by_id = {
        str(task.id): task
        for task in [_coerce_task(row) for row in (getattr(task_resp, "data", None) or [])]
    }

    preferred_mode = "mapbox"
    items: list[RouteVisualizationItem] = []
    for driver in target_drivers:
        driver_id = str(driver.id)
        best_path_nodes = _LATEST_BEST_PATH_NODES_BY_DRIVER.get(driver_id, [])
        if not best_path_nodes:
            best_path_nodes = _ensure_best_path_cached(driver)
        if not best_path_nodes:
            continue

        try:
            geometry, distance_m, duration_s, navigation = _build_route_geometry_for_driver(
                driver=driver,
                all_tasks_by_id=all_tasks_by_id,
                best_path_nodes=best_path_nodes,
                mode=preferred_mode,
            )
        except Exception:
            continue

        color = _color_for_driver(driver_id) if view_mode == "admin" else _DRIVER_IOS_BLUE
        pickup_points, dropoff_points = _extract_pickup_dropoff_points(
            best_path_nodes=best_path_nodes,
            all_tasks_by_id=all_tasks_by_id,
        )
        items.append(
            RouteVisualizationItem(
                driver_id=driver_id,
                best_path_nodes=best_path_nodes,
                geometry=geometry,
                distance_m=distance_m,
                duration_s=duration_s,
                color_hint=color,
                driver_start_location=[float(driver.start_location[0]), float(driver.start_location[1])],
                pickup_points=pickup_points,
                dropoff_points=dropoff_points,
                next_instruction=(navigation or {}).get("instruction"),
                next_road_name=(navigation or {}).get("road_name"),
                next_distance_m=(navigation or {}).get("distance_m"),
                next_maneuver_modifier=(navigation or {}).get("maneuver_modifier"),
                next_speed_limit_kmh=(navigation or {}).get("speed_limit_kmh"),
            )
        )

    return RouteVisualizationResponse(view_mode=view_mode, routes=items)
