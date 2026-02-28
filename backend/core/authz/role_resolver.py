from dataclasses import dataclass
from typing import Any, Literal

from backend.config import ROLE_FALLBACK_ENABLED
from backend.utils.supabase_client import supabase

RoleType = Literal["admin", "driver"]
RoleSource = Literal["profile", "metadata", "default"]


@dataclass
class RoleResolution:
    role: RoleType
    source: RoleSource


def _normalize_role(role: Any) -> RoleType:
    if role == "admin":
        return "admin"
    return "driver"


def resolve_role(user_id: str, user_metadata: dict[str, Any] | None = None) -> RoleResolution:
    metadata_role = _normalize_role((user_metadata or {}).get("role"))
    fallback_role = metadata_role if ROLE_FALLBACK_ENABLED else "driver"
    fallback_source: RoleSource = "metadata" if ROLE_FALLBACK_ENABLED else "default"

    try:
        profile_resp = (
            supabase.table("profile").select("role").eq("id", user_id).limit(1).execute()
        )
        rows = getattr(profile_resp, "data", None) or []
        if rows:
            return RoleResolution(role=_normalize_role(rows[0].get("role")), source="profile")
    except Exception as e:
        print(f"Warning: failed to read role from profile for {user_id}: {e}")

    return RoleResolution(role=fallback_role, source=fallback_source)
