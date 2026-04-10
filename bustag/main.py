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
    seed_urls = source.build_page_urls(1, 1)
    if not seed_urls:
        seed_urls = [root_url]

    asyncio.run(
        async_download(
            seed_urls,
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


@click.command(name='serve-api')
@click.option('--host', default='0.0.0.0', show_default=True, help='FastAPI 监听地址')
@click.option('--port', default=8001, show_default=True, type=int, help='FastAPI 监听端口')
@click.option('--reload', is_flag=True, help='开启 uvicorn 自动重载（开发环境）')
@click.option('--start-background-scheduler/--no-start-background-scheduler', default=False, show_default=True)
def serve_api(host, port, reload, start_background_scheduler):
    """启动 FastAPI 双栈 API（迁移阶段使用）"""
    import uvicorn

    from bustag.app.fastapi_app import create_fastapi_app

    app = create_fastapi_app(start_background_scheduler=start_background_scheduler)
    uvicorn.run(app, host=host, port=port, reload=reload)


def _serve_bottle_web(host: str, port: int, start_background_scheduler: bool):
    from bustag.app.index import start_app

    start_app(
        host=host,
        port=port,
        debug=False,
        start_background_scheduler=start_background_scheduler,
    )


def _serve_fastapi_web(host: str, port: int, reload: bool, start_background_scheduler: bool):
    import uvicorn

    from bustag.app.fastapi_app import create_fastapi_app

    app = create_fastapi_app(start_background_scheduler=start_background_scheduler)
    uvicorn.run(app, host=host, port=port, reload=reload)


@click.command(name='serve-web')
@click.option('--stack', type=click.Choice(['bottle', 'fastapi']), default='bottle', show_default=True, help='Web 栈类型')
@click.option('--host', default='127.0.0.1', show_default=True, help='监听地址')
@click.option('--port', default=8000, show_default=True, type=int, help='监听端口')
@click.option('--reload', is_flag=True, help='仅 fastapi 栈支持自动重载')
@click.option('--start-background-scheduler/--no-start-background-scheduler', default=False, show_default=True)
def serve_web(stack, host, port, reload, start_background_scheduler):
    """统一启动 Bottle/FastAPI Web 服务（发布门禁与本地演练）"""
    if stack == 'fastapi':
        _serve_fastapi_web(
            host=host,
            port=port,
            reload=reload,
            start_background_scheduler=start_background_scheduler,
        )
        return
    _serve_bottle_web(
        host=host,
        port=port,
        start_background_scheduler=start_background_scheduler,
    )


@click.group()
def main():
    pass


main.add_command(download)
main.add_command(recommend)
main.add_command(migrate)
main.add_command(migrate_status)
main.add_command(serve_api)
main.add_command(serve_web)

if __name__ == '__main__':
    main()
