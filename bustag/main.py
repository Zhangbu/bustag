'''
entry point for command line
'''

import asyncio
from pathlib import Path

import click

import bustag.model.classifier as clf
from bustag.spider import db as spider_db
from bustag.spider.crawler import async_download
from bustag.spider.migrate import apply_sql_migrations, get_migration_status
from bustag.spider.sources import get_source
from bustag.util import APP_CONFIG, init as init_app_config, logger

init_app_config()


def _ensure_db_ready():
    spider_db.init()


@click.command()
def recommend():
    '''
    根据现有模型预测推荐数据
    '''
    _ensure_db_ready()
    try:
        clf.recommend()
    except FileNotFoundError:
        click.echo('还没有训练好的模型, 无法推荐')


@click.command()
@click.option('--count', help='下载数量', type=int)
def download(count):
    """
    下载更新数据
    """
    _ensure_db_ready()

    print('start download')
    if count is not None:
        APP_CONFIG['download.count'] = count

    root_url = APP_CONFIG.get('download.root_path')
    if not root_url:
        logger.error('No root URL configured')
        return

    count_val = int(APP_CONFIG.get('download.count', 100))

    source = get_source()
    source.configure(root_url)

    asyncio.run(
        async_download(
            [root_url],
            count_val,
            router=source.router,
            fetcher=source.fetch,
            url_normalizer=source.normalize_url,
        )
    )


@click.command()
@click.option('--dry-run', is_flag=True, help='只检查待执行迁移，不实际执行')
@click.option('--migrations-dir', type=click.Path(file_okay=False, path_type=Path), help='自定义迁移目录')
@click.option('--backup/--no-backup', default=True, help='迁移前是否自动备份数据库')
@click.option('--backup-dir', type=click.Path(file_okay=False, path_type=Path), help='数据库备份目录')
def migrate(dry_run, migrations_dir, backup, backup_dir):
    """执行数据库 SQL 迁移"""
    result = apply_sql_migrations(
        migrations_dir=migrations_dir,
        dry_run=dry_run,
        backup_before_migrate=backup,
        backup_dir=backup_dir,
    )

    click.echo(f"db: {result['db_path']}")
    click.echo(f"migrations: {result['migrations_dir']}")
    click.echo(f"backup enabled: {result['backup_enabled']}")
    if result['backup_path']:
        click.echo(f"backup file: {result['backup_path']}")

    if dry_run:
        click.echo('dry-run mode')

    click.echo(f"total: {result['total']}")
    click.echo(f"pending: {len(result['pending'])}")
    if result['pending']:
        for name in result['pending']:
            click.echo(f"  - {name}")

    if not dry_run:
        click.echo(f"applied: {len(result['applied'])}")
        if result['applied']:
            for name in result['applied']:
                click.echo(f"  + {name}")


@click.command(name='migrate-status')
@click.option('--migrations-dir', type=click.Path(file_okay=False, path_type=Path), help='自定义迁移目录')
def migrate_status(migrations_dir):
    """查看数据库迁移状态"""
    result = get_migration_status(migrations_dir=migrations_dir)

    click.echo(f"db: {result['db_path']}")
    click.echo(f"migrations: {result['migrations_dir']}")
    click.echo(f"total: {result['total']}")
    click.echo(f"applied: {len(result['applied'])}")
    if result['applied']:
        for name in result['applied']:
            click.echo(f"  + {name}")
    click.echo(f"pending: {len(result['pending'])}")
    if result['pending']:
        for name in result['pending']:
            click.echo(f"  - {name}")


@click.group()
def main():
    pass


main.add_command(download)
main.add_command(recommend)
main.add_command(migrate)
main.add_command(migrate_status)

if __name__ == '__main__':
    main()
