from fastapi import FastAPI
from backend.api.routers import driver
from backend.api.routers import task
from backend.api.routers import aco_optimizer
from backend.api.routers import route
from backend.features.route_optimization.aco_optimizer import ACOOptimizer

app = FastAPI(
    title="Hack of Humanity API",
    description="Carbon Emission Reduction API",
    version="1.0.0"
)

app.include_router(driver.router, prefix="/api", tags=["drivers"])
app.include_router(task.router, prefix="/api", tags=["tasks"])
app.include_router(aco_optimizer.router, prefix="/api", tags=["optimization"])
app.include_router(route.router, prefix="/api", tags=["routing"])

@app.get("/")
def root():
    return {
        "message": "Hack of Humanity API is running",
        "version": "1.0.0",
        "status": "healthy"
    }

def main():
    ACOOptimizer.solve()

if __name__ == "__main__":
    main()
