from abc import ABC, abstractmethod
from typing import List, Dict, Any


class BaseRepository(ABC):
    """
    Base persistence interface.
    All storage backends must implement this.
    """

    @abstractmethod
    def save_driver(self, driver: Dict[str, Any]) -> None:
        pass

    @abstractmethod
    def save_task(self, task: Dict[str, Any]) -> None:
        pass

    @abstractmethod
    def save_route_result(self, route_data: Dict[str, Any]) -> None:
        pass

    @abstractmethod
    def load_drivers(self) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def load_tasks(self) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def load_routes(self) -> List[Dict[str, Any]]:
        pass