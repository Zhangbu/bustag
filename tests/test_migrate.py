import sqlite3
from pathlib import Path

import pytest

from bustag.spider.migrate import apply_sql_migrations


def test_apply_sql_migrations_dry_run_and_apply(tmp_path: Path):
    db_path = tmp_path / 'test.db'
    backup_dir = tmp_path / 'backups'
    migrations_dir = tmp_path / 'migrations'
    migrations_dir.mkdir()

    (migrations_dir / '0001_create_demo.sql').write_text(
        'CREATE TABLE IF NOT EXISTS demo (id INTEGER PRIMARY KEY, name TEXT);',
        encoding='utf-8',
    )

    dry_result = apply_sql_migrations(
        db_path=str(db_path),
        migrations_dir=migrations_dir,
        dry_run=True,
        backup_dir=backup_dir,
    )
    assert dry_result['pending'] == ['0001_create_demo.sql']
    assert dry_result['applied'] == []
    assert dry_result['backup_path'] is None

    apply_result = apply_sql_migrations(
        db_path=str(db_path),
        migrations_dir=migrations_dir,
        dry_run=False,
        backup_dir=backup_dir,
    )
    assert apply_result['applied'] == ['0001_create_demo.sql']
    assert apply_result['backup_path'] is not None

    apply_again = apply_sql_migrations(
        db_path=str(db_path),
        migrations_dir=migrations_dir,
        dry_run=False,
        backup_dir=backup_dir,
    )
    assert apply_again['applied'] == []
    assert apply_again['pending'] == []
    assert apply_again['backup_path'] is not None


def test_migration_failure_restores_backup(tmp_path: Path):
    db_path = tmp_path / 'test.db'
    backup_dir = tmp_path / 'backups'
    migrations_dir = tmp_path / 'migrations'
    migrations_dir.mkdir()

    conn = sqlite3.connect(db_path)
    conn.execute('CREATE TABLE seed (id INTEGER PRIMARY KEY, name TEXT)')
    conn.execute("INSERT INTO seed(name) VALUES ('before')")
    conn.commit()
    conn.close()

    (migrations_dir / '0001_add_col.sql').write_text(
        'ALTER TABLE seed ADD COLUMN note TEXT;',
        encoding='utf-8',
    )
    (migrations_dir / '0002_broken.sql').write_text(
        'THIS IS INVALID SQL;',
        encoding='utf-8',
    )

    with pytest.raises(sqlite3.DatabaseError):
        apply_sql_migrations(
            db_path=str(db_path),
            migrations_dir=migrations_dir,
            dry_run=False,
            backup_before_migrate=True,
            backup_dir=backup_dir,
        )

    backups = sorted(backup_dir.glob('*.bak*.db'))
    assert backups, 'backup file should be created before applying migrations'

    conn = sqlite3.connect(db_path)
    cols = [row[1] for row in conn.execute('PRAGMA table_info(seed)').fetchall()]
    value = conn.execute('SELECT name FROM seed WHERE id = 1').fetchone()[0]
    conn.close()

    assert cols == ['id', 'name']
    assert value == 'before'
