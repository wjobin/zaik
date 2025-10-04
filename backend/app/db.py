"""
Database module for Zaik game.

Handles TinyDB initialization, connection management, and database utilities.
"""

from pathlib import Path
from typing import Optional
from tinydb import TinyDB, Query
import os


class Database:
    """Database manager for Zaik game state."""

    _instance: Optional['Database'] = None
    _db: Optional[TinyDB] = None

    def __new__(cls):
        """Singleton pattern to ensure single database instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize database connection."""
        if self._db is None:
            db_path = self._get_db_path()
            self._db = TinyDB(db_path)

    def _get_db_path(self) -> Path:
        """Get database file path from environment or use default."""
        db_dir = os.getenv('ZAIK_DB_DIR', 'data')
        db_name = os.getenv('ZAIK_DB_NAME', 'zaik.json')

        # Create data directory if it doesn't exist
        db_path = Path(db_dir)
        db_path.mkdir(parents=True, exist_ok=True)

        return db_path / db_name

    @property
    def db(self) -> TinyDB:
        """Get the database instance."""
        if self._db is None:
            raise RuntimeError("Database not initialized")
        return self._db

    def close(self):
        """Close database connection."""
        if self._db:
            self._db.close()
            self._db = None

    def reset(self):
        """Reset database by clearing all tables."""
        if self._db:
            self._db.drop_tables()

    def recreate(self):
        """Recreate database from scratch."""
        self.close()
        db_path = self._get_db_path()
        if db_path.exists():
            db_path.unlink()
        self.__init__()


# Convenience functions for accessing database
def get_db() -> TinyDB:
    """Get the database instance."""
    return Database().db


def init_db():
    """Initialize the database (called on application startup)."""
    Database()


def close_db():
    """Close database connection (called on application shutdown)."""
    Database().close()


def reset_db():
    """Reset database by clearing all data."""
    Database().reset()


def recreate_db():
    """Recreate database from scratch."""
    Database().recreate()
