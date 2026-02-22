from .json_repository import JSONRepository
from .sqlite_repository import SQLiteRepository


def get_repository(storage_type: str = "json"):
    if storage_type == "sqlite":
        return SQLiteRepository()
    return JSONRepository()