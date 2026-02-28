from dataclasses import dataclass

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from backend.core.authz.role_resolver import RoleType, RoleSource, resolve_role
from backend.utils.supabase_client import supabase

security = HTTPBearer(auto_error=False)


@dataclass
class RequestUser:
    user_id: str
    role: RoleType
    role_source: RoleSource


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> RequestUser:
    if credentials is None or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "auth_missing_token",
                "category": "authentication",
                "message": "Missing access token.",
                "retryable": False,
            },
        )

    token = credentials.credentials
    try:
        user_response = supabase.auth.get_user(token)
        user = user_response.user
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "auth_invalid_token",
                "category": "authentication",
                "message": f"Invalid access token: {e}",
                "retryable": False,
            },
        ) from e

    if user is None or not getattr(user, "id", None):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "auth_user_not_found",
                "category": "authentication",
                "message": "Unable to resolve user from token.",
                "retryable": False,
            },
        )

    user_id = str(user.id)
    user_metadata = getattr(user, "user_metadata", None) or {}
    role_resolution = resolve_role(user_id, user_metadata=user_metadata)
    return RequestUser(
        user_id=user_id,
        role=role_resolution.role,
        role_source=role_resolution.source,
    )
