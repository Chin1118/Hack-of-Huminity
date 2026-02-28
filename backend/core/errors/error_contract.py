from typing import Any


def api_error(
    code: str,
    message: str,
    *,
    category: str,
    retryable: bool = False,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    detail = {
        "code": code,
        "category": category,
        "message": message,
        "retryable": retryable,
    }
    if context:
        detail["context"] = context
    return detail
