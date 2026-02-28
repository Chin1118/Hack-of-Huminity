from fastapi import HTTPException, status

from backend.core.authz.dependencies import RequestUser


def ensure_admin(current_user: RequestUser, detail: str = "Admin role required.") -> None:
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "forbidden_admin_required",
                "category": "authorization",
                "message": detail,
                "retryable": False,
            },
        )


def ensure_self_or_admin(
    current_user: RequestUser,
    owner_user_id: str,
    detail: str = "Not allowed to access this resource.",
) -> None:
    if current_user.role == "admin":
        return
    if current_user.user_id != owner_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "forbidden_owner_mismatch",
                "category": "authorization",
                "message": detail,
                "retryable": False,
            },
        )
