from fastapi import FastAPI
from backend.api.routers import driver

app = FastAPI(
    title="Hack of Humanity API",
    description="Carbon Emission Reduction API",
    version="1.0.0"
)

app.include_router(driver.router, prefix="/api", tags=["drivers"])

@app.get("/")
def root():
    return {
        "message": "Hack of Humanity API is running",
        "version": "1.0.0",
        "status": "healthy"
    }
