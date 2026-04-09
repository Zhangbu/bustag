"""SQLite SQL migration runner for bustag."""
from __future__ import annotations

import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from bustag.util import get_data_path, logger

MIGRATIONS_TABLE = 'schema_migrations'


def _default_migrations_dir() -> Path:
    return Path(__file__).resolve().parents[2] / 'migrations' / 'sql'


def _ensure_migrations_table(conn: sqlite3.Connection):
    conn.execute(
        f'''
        CREATE TABLE IF NOT EXISTS {MIGRATIONS_TABLE} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            applied_at TEXT NOT NULL
        )
        '''
    )
    conn.commit()


def _discover_migrations(migrations_dir: Path) -> list[Path]:
    if not migrations_dir.exists():
        return []
    return sorted(path for path in migrations_dir.glob('*.sql') if path.is_file())


def _load_applied_migrations(conn: sqlite3.Connection) -> set[str]:
    rows = conn.execute(f'SELECT name FROM {MIGRATIONS_TABLE}').fetchall()
    return {row[0] for row in rows}


def _record_migration(conn: sqlite3.Connection, name: str):
    conn.execute(
        f'INSERT INTO {MIGRATIONS_TABLE}(name, applied_at) VALUES (?, ?)',
        (name, datetime.now(UTC).isoformat()),
    )


def apply_sql_migrations(
    db_path: str | None = None,
    migrations_dir: str | Path | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    db_file = db_path or get_data_path('bus.db')
    migration_dir = Path(migrations_dir) if migrations_dir else _default_migrations_dir()

    migration_dir.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(db_file)
    try:
        _ensure_migrations_table(conn)
        applied = _load_applied_migrations(conn)
        migrations = _discover_migrations(migration_dir)

        pending = [m for m in migrations if m.name not in applied]
        newly_applied: list[str] = []

        if not dry_run:
            for migration_file in pending:
                sql = migration_file.read_text(encoding='utf-8')
                logger.info('Applying migration: %s', migration_file.name)
                with conn:
                    conn.executescript(sql)
                    _record_migration(conn, migration_file.name)
                newly_applied.append(migration_file.name)

        return {
            'db_path': str(Path(db_file).resolve()),
            'migrations_dir': str(migration_dir.resolve()),
            'dry_run': dry_run,
            'applied': newly_applied,
            'pending': [m.name for m in pending],
            'total': len(migrations),
        }
    finally:
        conn.close()
