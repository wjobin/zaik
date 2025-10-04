# Database Migrations

This directory contains database migration scripts for the Zaik game.

## Creating a Migration

1. Create a new file named `{version}_{description}.py` where version is a zero-padded number (e.g., `001_initial_setup.py`)

2. Define an `up` function that takes a TinyDB instance:

```python
from tinydb import TinyDB

def up(db: TinyDB):
    """
    Apply the migration.

    Example: Initialize game_state table with default data
    """
    game_state_table = db.table('game_state')
    game_state_table.insert({
        'version': 1,
        'initialized': True
    })
```

## Running Migrations

From the backend directory:

```bash
python -m app.cli migrate
```

Or programmatically:

```python
from app.db import get_db
from app.migrations.manager import MigrationManager

db = get_db()
manager = MigrationManager(db)
manager.load_migration_files()
manager.migrate()
```

## Migration Best Practices

1. **Never modify existing migrations** - Once applied, migrations should not be changed
2. **Keep migrations small and focused** - One logical change per migration
3. **Test migrations before committing** - Always test on a copy of production data
4. **Document breaking changes** - Add comments explaining any major schema changes
5. **Make migrations idempotent when possible** - Check before creating/modifying data

## Example Migration Structure

```
migrations/
├── __init__.py
├── manager.py
├── README.md
├── 001_initial_setup.py
├── 002_add_locations_table.py
└── 003_add_inventory_system.py
```
