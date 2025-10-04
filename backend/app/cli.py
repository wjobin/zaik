"""
Command-line interface for Zaik database management.

Usage:
    python -m app.cli migrate       # Run pending migrations
    python -m app.cli reset         # Clear all database data
    python -m app.cli recreate      # Recreate database from scratch
"""

import sys
from pathlib import Path
from .db import get_db, reset_db, recreate_db, init_db
from .migrations.manager import MigrationManager


def migrate():
    """Run all pending migrations."""
    print("Running database migrations...")
    init_db()
    db = get_db()

    manager = MigrationManager(db)
    manager.load_migration_files()

    pending = manager.get_pending_migrations()
    if not pending:
        print("✓ No pending migrations")
        return

    print(f"Found {len(pending)} pending migration(s)")
    manager.migrate()
    print("✓ All migrations applied successfully")


def reset():
    """Reset database by clearing all data."""
    print("Resetting database...")
    init_db()
    reset_db()
    print("✓ Database reset complete")


def recreate():
    """Recreate database from scratch."""
    print("Recreating database...")
    recreate_db()
    print("✓ Database recreated")


def show_status():
    """Show database status and migration info."""
    init_db()
    db = get_db()

    manager = MigrationManager(db)
    manager.load_migration_files()

    applied = manager.get_applied_migrations()
    pending = manager.get_pending_migrations()

    print("Database Status")
    print("=" * 50)
    print(f"Applied migrations: {len(applied)}")
    for m in applied:
        print(f"  ✓ {m['version']}: {m['name']} (applied: {m['applied_at']})")

    if pending:
        print(f"\nPending migrations: {len(pending)}")
        for m in pending:
            print(f"  ○ {m.version}: {m.name}")
    else:
        print("\n✓ No pending migrations")


def main():
    """Main CLI entry point."""
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    command = sys.argv[1]

    commands = {
        'migrate': migrate,
        'reset': reset,
        'recreate': recreate,
        'status': show_status,
    }

    if command not in commands:
        print(f"Unknown command: {command}")
        print(__doc__)
        sys.exit(1)

    try:
        commands[command]()
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
