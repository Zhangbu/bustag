from pathlib import Path

from bustag.spider.migrate import apply_sql_migrations


def test_apply_sql_migrations_dry_run_and_apply(tmp_path: Path):
    db_path = tmp_path / 'test.db'
    migrations_dir = tmp_path / 'migrations'
    migrations_dir.mkdir()

    (migrations_dir / '0001_create_demo.sql').write_text(
        'CREATE TABLE IF NOT EXISTS demo (id INTEGER PRIMARY KEY, name TEXT);',
        encoding='utf-8',
    )

    dry_result = apply_sql_migrations(db_path=str(db_path), migrations_dir=migrations_dir, dry_run=True)
    assert dry_result['pending'] == ['0001_create_demo.sql']
    assert dry_result['applied'] == []

    apply_result = apply_sql_migrations(db_path=str(db_path), migrations_dir=migrations_dir, dry_run=False)
    assert apply_result['applied'] == ['0001_create_demo.sql']

    apply_again = apply_sql_migrations(db_path=str(db_path), migrations_dir=migrations_dir, dry_run=False)
    assert apply_again['applied'] == []
    assert apply_again['pending'] == []
