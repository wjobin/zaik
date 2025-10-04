"""
Migration manager for database schema changes.

Provides a simple migration system for TinyDB that tracks applied migrations
and allows for forward migrations.
"""

from pathlib import Path
from typing import List, Callable
from datetime import datetime
import importlib.util
import sys
from tinydb import TinyDB


class Migration:
    """Represents a single database migration."""

    def __init__(self, version: str, name: str, up: Callable[[TinyDB], None]):
        """
        Initialize a migration.

        Args:
            version: Version string (e.g., '001', '002')
            name: Descriptive name for the migration
            up: Function that performs the migration
        """
        self.version = version
        self.name = name
        self.up = up
        self.applied_at: str | None = None


class MigrationManager:
    """Manages database migrations."""

    MIGRATIONS_TABLE = '_migrations'

    def __init__(self, db: TinyDB, migrations_dir: Path | None = None):
        """
        Initialize migration manager.

        Args:
            db: TinyDB instance
            migrations_dir: Directory containing migration files
        """
        self.db = db
        self.migrations_dir = migrations_dir or Path(__file__).parent
        self.migrations: List[Migration] = []

    def register_migration(self, version: str, name: str, up: Callable[[TinyDB], None]):
        """
        Register a migration.

        Args:
            version: Version string (e.g., '001', '002')
            name: Descriptive name
            up: Migration function
        """
        migration = Migration(version, name, up)
        self.migrations.append(migration)

    def _get_migrations_table(self):
        """Get the migrations tracking table."""
        return self.db.table(self.MIGRATIONS_TABLE)

    def _is_applied(self, version: str) -> bool:
        """Check if a migration version has been applied."""
        migrations_table = self._get_migrations_table()
        from tinydb import Query
        Migration = Query()
        result = migrations_table.search(Migration.version == version)
        return len(result) > 0

    def _mark_applied(self, version: str, name: str):
        """Mark a migration as applied."""
        migrations_table = self._get_migrations_table()
        migrations_table.insert({
            'version': version,
            'name': name,
            'applied_at': datetime.utcnow().isoformat()
        })

    def get_applied_migrations(self) -> List[dict]:
        """Get list of applied migrations."""
        migrations_table = self._get_migrations_table()
        return migrations_table.all()

    def get_pending_migrations(self) -> List[Migration]:
        """Get list of pending migrations."""
        return [m for m in sorted(self.migrations, key=lambda x: x.version)
                if not self._is_applied(m.version)]

    def migrate(self):
        """Run all pending migrations."""
        pending = self.get_pending_migrations()

        if not pending:
            print("No pending migrations")
            return

        for migration in pending:
            print(f"Applying migration {migration.version}: {migration.name}")
            try:
                migration.up(self.db)
                self._mark_applied(migration.version, migration.name)
                print(f"✓ Migration {migration.version} applied successfully")
            except Exception as e:
                print(f"✗ Migration {migration.version} failed: {e}")
                raise

    def load_migration_files(self):
        """
        Load migration files from the migrations directory.

        Migration files should be named: {version}_{name}.py
        Example: 001_initial_setup.py

        Each file should define an `up(db: TinyDB)` function.
        """
        migration_files = sorted(self.migrations_dir.glob('[0-9]*.py'))

        for file_path in migration_files:
            if file_path.name.startswith('_'):
                continue

            # Extract version from filename
            version = file_path.stem.split('_')[0]
            name = '_'.join(file_path.stem.split('_')[1:])

            # Load the module
            spec = importlib.util.spec_from_file_location(f"migration_{version}", file_path)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                sys.modules[f"migration_{version}"] = module
                spec.loader.exec_module(module)

                # Get the up function
                if hasattr(module, 'up'):
                    self.register_migration(version, name, module.up)
                else:
                    print(f"Warning: Migration {file_path.name} has no 'up' function")
