import json
from typing import List
from fastapi import APIRouter, HTTPException, status
from pydantic import ValidationError
from pydantic import BaseModel

from backend.utils.road_network import RoadNetwork
from backend.utils.route_data_loader import load_route_seed_data

router = APIRouter(tags=["routing"])


class GetRouteRequest(BaseModel):
    ordered_node_ids: List[str]


@router.post("/get-route")
def get_route(req: GetRouteRequest):
    if not req.ordered_node_ids or len(req.ordered_node_ids) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ordered_node_ids must contain at least 2 node IDs.",
        )

    if not all(isinstance(node_id, str) and node_id.strip() for node_id in req.ordered_node_ids):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ordered_node_ids must be a list of non-empty strings.",
        )

    try:
        drivers, tasks = load_route_seed_data()
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Route seed file missing: {exc}",
        ) from exc
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Invalid JSON in route seed data: {exc}",
        ) from exc
    except (ValueError, ValidationError) as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Invalid route seed schema: {exc}",
        ) from exc

    try:
        network = RoadNetwork(drivers=drivers, tasks=tasks, mode="mapbox")
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initialize road network: {exc}",
        ) from exc

    try:
        route_data = network.get_tour_route(req.ordered_node_ids)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid route input: {exc}",
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Route generation failed: {exc}",
        ) from exc

    if not route_data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Route generation returned no data.",
        )

    try:
        route = route_data["routes"][0]
        coordinates = route["geometry"]["coordinates"]
        duration = route["duration"]
        distance = route["distance"]
    except (KeyError, IndexError, TypeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Unexpected response format from route provider.",
        ) from exc

    return {
        "status": "success",
        "coordinates": coordinates,
        "duration": duration,
        "distance": distance,
    }
