# Bustag 渐进式重构清单（执行版）

## 目标

- 先稳定，再解耦，再升级技术栈。
- 每个阶段都可回滚、可验证。

## 里程碑

- [x] M1: 基线护栏（测试补齐、CI 门禁基础）
- [x] M2: 启动生命周期显式化（`create_app` + 显式 init）
- [x] M3: 生产运行现代化（gunicorn + `/healthz`）
- [x] M4: 任务队列化（抓取/训练/推荐异步任务）
  - [x] Phase 1: 引入应用内任务队列 + 调度/手动拉取异步提交 + 任务状态查询
  - [x] Phase 2: 模型训练异步化 + 模型页任务状态展示
  - [x] Phase 3: 队列后端可替换抽象（默认 memory，无中间件依赖）
- [x] M5: 数据库迁移体系（migrations）
  - [x] Phase 1: SQL migration runner + baseline migration + CLI/Makefile 接入
  - [x] Phase 2: 迁移前自动备份 + 失败自动回滚恢复 + 安全迁移脚本
  - [x] Phase 3: 生产发布迁移流程文档化 + 迁移状态核对命令
- [ ] M6: FastAPI 双栈迁移
  - [x] Phase 1: 新增 FastAPI 最小 API（/healthz、/task/{task_id}）+ CLI 启动命令
  - [ ] Phase 2: 抽取共享 service 层，消除 Bottle/FastAPI 业务重复
  - [ ] Phase 3: 鉴权、错误模型、可观测性统一并评估默认入口切换

## M1 交付项

- 新增生命周期测试：`tests/test_app_lifecycle.py`
- 测试夹具显式初始化数据库：`tests/conftest.py`

## M2 交付项

- Web 入口改为显式生命周期初始化：`bustag/app/index.py`
  - `initialize_runtime()`
  - `create_app()`
- 移除数据库导入时自动初始化：`bustag/spider/db.py`
- CLI 显式初始化配置和数据库：`bustag/main.py`

## M3 交付项

- 新增 WSGI 入口：`bustag/app/wsgi.py`
- 新增健康检查路由：`/healthz`
- Docker 入口切换为 gunicorn：`docker/entry.sh`
- 补充运行时环境变量示例：`.env.example`

## M4 交付项（当前实现为无中间件方案）

- 新增轻量任务队列：`bustag/app/tasks.py`
- 调度器下载任务异步提交：`bustag/app/schedule.py`
- 手动拉取改为后台任务提交并返回任务ID：`/fetch`
- 模型训练改为后台任务提交并返回任务ID：`/do-training`
- 新增任务状态查询接口：`/task/<task_id>`
- 模型页新增训练任务状态展示：`bustag/app/views/model.tpl`
- 任务队列后端抽象：`TaskBackend` + `create_task_queue*`（默认 `memory`，未知后端自动回退）
- 任务与调度测试：`tests/test_tasks.py`、`tests/test_tasks_backend.py`、`tests/test_schedule_async.py`、`tests/test_model_async.py`

## M5 交付项

- 迁移执行器：`bustag/spider/migrate.py`
- 基线 SQL 迁移：`migrations/sql/0001_baseline_schema.sql`
- CLI 命令：`python -m bustag.main migrate [--dry-run] [--backup/--no-backup]`
- 状态命令：`python -m bustag.main migrate-status`
- Makefile 命令：`migrate`、`migrate-dry-run`、`migrate-safe`、`migrate-status`
- 安全迁移脚本：`scripts/migrate.sh`
- 失败回滚能力：迁移失败自动从备份恢复
- 迁移 runbook：`docs/MIGRATION_RUNBOOK.md`
- 迁移测试：`tests/test_migrate.py`

## M6 交付项（Phase 1）

- FastAPI 最小入口：`bustag/app/fastapi_app.py`
- 最小 API：`GET /healthz`、`GET /task/{task_id}`
- CLI 启动命令：`python -m bustag.main serve-api`
- 依赖补齐：`fastapi`、`uvicorn`
- 测试覆盖：`tests/test_fastapi_app.py`、`tests/test_main.py`

## 回滚策略

1. 回滚 `bustag/spider/migrate.py` 与 `migrations/sql/*` 可恢复到无迁移执行器状态。
2. 回滚 `bustag/main.py`、`Makefile`、`scripts/migrate.sh` 可移除迁移命令和安全脚本入口。
3. 所有改动已集中在单一分支，支持整分支回退。
