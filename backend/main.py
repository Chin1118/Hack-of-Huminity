from typing import Literal

from fastapi import APIRouter, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.api.routers import driver
from backend.api.routers import task
from backend.api.routers import aco_optimizer
from backend.core.authz.role_resolver import resolve_role
from backend.core.errors.error_contract import api_error
from backend.features.route_optimization.aco_optimizer import ACOOptimizer
from backend.utils.login import SignupError, login_user, logout_user, sign_up_user
from backend.utils.supabase_client import supabase

app = FastAPI(
    title="Hack of Humanity API",
    description="Carbon Emission Reduction API",
    version="1.0.0"
)

app.include_router(driver.router, prefix="/api", tags=["drivers"])
app.include_router(task.router, prefix="/api", tags=["tasks"])
app.include_router(aco_optimizer.router, prefix="/api", tags=["optimization"])


class LoginRequest(BaseModel):
    email: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    user_id: str
    name: str
    email: str
    role: Literal["admin", "driver"]
    is_admin: bool


class SignupRequest(BaseModel):
    name: str | None = None
    email: str
    password: str


class SignupResponse(BaseModel):
    email: str
    message: str


class LogoutResponse(BaseModel):
    message: str


auth_router = APIRouter(prefix="/api/auth", tags=["auth"])


@auth_router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest) -> LoginResponse:
    login_result = login_user(payload.email, payload.password)
    if not login_result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    access_token = login_result["access_token"]
    user_response = supabase.auth.get_user(access_token)
    user = user_response.user
    user_metadata = getattr(user, "user_metadata", None) or {}
    role = resolve_role(login_result["user_id"], user_metadata).role
    email = getattr(user, "email", None) or payload.email
    name = str(user_metadata.get("name") or "").strip() or email.split("@")[0]

    return LoginResponse(
        access_token=login_result["access_token"],
        refresh_token=login_result["refresh_token"],
        user_id=login_result["user_id"],
        name=name,
        email=email,
        role=role,
        is_admin=role == "admin",
    )


@auth_router.post("/signup", response_model=SignupResponse, status_code=status.HTTP_201_CREATED)
def signup(payload: SignupRequest) -> SignupResponse:
    try:
        sign_up_user(payload.email, payload.password, payload.name)
    except SignupError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=api_error(
                "signup_failed",
                f"Signup failed: {e.message}",
                category="authentication",
            ),
        )

    return SignupResponse(
        email=payload.email,
        message="Signup successful. Please verify your email before logging in.",
    )


@auth_router.post("/logout", response_model=LogoutResponse)
def logout() -> LogoutResponse:
    logged_out = logout_user()
    if not logged_out:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=api_error(
                "logout_failed",
                "Logout failed on auth provider.",
                category="upstream",
                retryable=True,
            ),
        )
    return LogoutResponse(message="Logged out successfully.")


app.include_router(auth_router)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
