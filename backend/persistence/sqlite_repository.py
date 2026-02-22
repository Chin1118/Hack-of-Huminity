import sqlite3
from typing import List, Dict, Any
from .base import BaseRepository


class SQLiteRepository(BaseRepository):

    def __init__(self, db_path="backend/data/system.db"):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self._create_tables()

    def _create_tables(self):
        cursor = self.conn.cursor()

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS drivers (
            id INTEGER PRIMARY KEY,
            data TEXT
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY,
            data TEXT
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS routes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data TEXT
        )
        """)

        self.conn.commit()

    def save_driver(self, driver: Dict[str, Any]) -> None:
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO drivers (id, data) VALUES (?, ?)",
            (driver["id"], str(driver))
        )
        self.conn.commit()

    def save_task(self, task: Dict[str, Any]) -> None:
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO tasks (id, data) VALUES (?, ?)",
            (task["id"], str(task))
        )
        self.conn.commit()

    def save_route_result(self, route_data: Dict[str, Any]) -> None:
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO routes (data) VALUES (?)",
            (str(route_data),)
        )
        self.conn.commit()

    def load_drivers(self) -> List[Dict[str, Any]]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT data FROM drivers")
        return [eval(row[0]) for row in cursor.fetchall()]

    def load_tasks(self) -> List[Dict[str, Any]]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT data FROM tasks")
        return [eval(row[0]) for row in cursor.fetchall()]

    def load_routes(self) -> List[Dict[str, Any]]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT data FROM routes")
        return [eval(row[0]) for row in cursor.fetchall()]