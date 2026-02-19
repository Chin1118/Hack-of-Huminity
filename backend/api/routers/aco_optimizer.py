from fastapi import APIRouter, HTTPException
from backend.api.schemas.aco_optimizer import SolveRequest, SolveResponse
from backend.api.converters.driver import find_driver_by_id
from backend.api.converters.task import load_tasks
from backend.utils.pheromone import load_pheromone_matrix  # 如果你有
from backend.features.route_optimization.aco_optimizer import ACOOptimizer

router = APIRouter(prefix="/optimization", tags=["optimization"])

@router.post("/solve", response_model=SolveResponse)
def solve(req: SolveRequest):
    driver = find_driver_by_id(req.driver_id)
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")

    tasks = load_tasks()
    pheromone_matrix = load_pheromone_matrix()  # 或默认 {}

    optimizer = ACOOptimizer(driver=driver, tasks=tasks, pheromone_matrix=pheromone_matrix)
    return optimizer.solve()
