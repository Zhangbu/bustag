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
- [x] M6: FastAPI 双栈迁移
  - [x] Phase 1: 新增 FastAPI 最小 API（/healthz、/task/{task_id}）+ CLI 启动命令
  - [x] Phase 2: 抽取共享 service 层，消除 Bottle/FastAPI 业务重复
  - [x] Phase 3: 鉴权、错误模型、可观测性统一并评估默认入口切换
- [x] M7: API 可靠性增强（灰度前）
  - [x] Phase 1: FastAPI 异常兜底与统一 500 错误模型
  - [x] Phase 2: API 指标埋点与慢请求阈值告警
  - [x] Phase 3: 灰度开关与回滚演练脚本
- [ ] M8: 默认切换发布治理
  - [x] Phase 1: 预发验收脚本（接口契约自动检查）
  - [x] Phase 2: 发布流水线门禁集成

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

## M6 交付项（Phase 1-3）

- FastAPI 最小入口：`bustag/app/fastapi_app.py`
- 最小 API：`GET /healthz`、`GET /task/{task_id}`
- CLI 启动命令：`python -m bustag.main serve-api`
- 依赖补齐：`fastapi`、`uvicorn`
- 共享 API service：`bustag/app/api_service.py`
- 测试覆盖：`tests/test_fastapi_app.py`、`tests/test_api_service.py`、`tests/test_main.py`

## 回滚策略

1. 回滚 `bustag/spider/migrate.py` 与 `migrations/sql/*` 可恢复到无迁移执行器状态。
2. 回滚 `bustag/main.py`、`Makefile`、`scripts/migrate.sh` 可移除迁移命令和安全脚本入口。
3. 所有改动已集中在单一分支，支持整分支回退。

## M6 默认入口评估（2026-04-09）

- 评估结论：当前默认入口继续保持 Bottle，FastAPI 作为并行 API 栈。
- 原因：主站页面路由与模板仍主要依赖 Bottle，直接切默认入口风险较高。
- 切换前置条件：
  - 完成页面路由/鉴权中间件等能力在 FastAPI 侧的等价实现。
  - 在预发环境完成请求量与错误率对比观测。
  - 提供一键回退到 Bottle 默认入口的发布开关。

## M7 交付项（Phase 1）

- FastAPI 中间件异常兜底：统一返回 `internal_error` 错误结构
- 异常响应保留请求链路 ID：`X-Request-ID`
- FastAPI 异常路径测试：`tests/test_fastapi_app.py::test_internal_error_has_unified_payload`

## M7 交付项（Phase 2）

- 共享 API 指标埋点：总请求、慢请求、按框架/路径/状态统计
- 慢请求阈值：`BUSTAG_API_SLOW_MS`（默认 800ms）
- Bottle/FastAPI 双栈统一慢请求告警日志
- 配置示例补充：`.env.example`

## M7 交付项（Phase 3）

- 运行栈开关：`BUSTAG_WEB_STACK=bottle|fastapi`
- 生产入口按栈选择：`bustag/app/wsgi.py` + `docker/entry.sh`
- 灰度/回滚演练脚本：`scripts/web_stack_drill.sh`
- 演练快捷命令：`make web-drill-fastapi` / `make web-drill-bottle`
- 栈选择测试：`tests/test_wsgi_stack.py`

## M8 交付项（Phase 1）

- 预发自动验收脚本：`scripts/pre_release_web_check.sh`
- 验收内容：`/healthz` 与 `/task/{missing}` 契约、状态码、`X-Request-ID`
- 演练命令：`make web-precheck-fastapi`、`make web-precheck-bottle`
- 切换 runbook：`docs/WEB_STACK_ROLLOUT.md`

## M8 交付项（Phase 2）

- 发布流水线门禁脚本：`scripts/release_web_gate.sh`
- 门禁命令：`make web-release-gate`
- 双栈自动验收：Bottle 通过 `serve-web` 真实启动验收，FastAPI 通过进程内契约验收（`fastapi.testclient`）
- CI 可配置项：`BUSTAG_GATE_HOST`、`BUSTAG_GATE_PORT`、`BUSTAG_GATE_WAIT_SECONDS`、`BUSTAG_GATE_STACKS`、`BUSTAG_GATE_ALLOW_SKIP_MISSING_FASTAPI`

## MissAV 稳定化（专项）

- 生产发布清单：`docs/PROD_RELEASE_CHECKLIST.md`
- MissAV 状态文档：`docs/MISSAV_STATUS.md`
- 依赖声明补齐：`curl_cffi`（`pyproject.toml`、`requirements.txt`）
- Source 懒加载降级：MissAV 依赖缺失不影响 `bus` 运行
- 探针命令：`make missav-probe`（`scripts/missav_probe.sh`）

## Crawler-Only（专项）

- 线上仅爬虫运行脚本：`scripts/crawler_once.sh`、`scripts/crawler_loop.sh`
- 数据快照导出/导入脚本：`scripts/export_crawler_data.sh`、`scripts/import_crawler_data.sh`
- 命令入口：`make crawler-once`、`make crawler-loop`、`make crawler-export`、`make crawler-import`
- 运行文档：`docs/CRAWLER_ONLY_RUNBOOK.md`
