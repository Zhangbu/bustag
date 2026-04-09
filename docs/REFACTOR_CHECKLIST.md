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
- [ ] M5: 数据库迁移体系（migrations）
- [ ] M6: FastAPI 双栈迁移

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

## 回滚策略

1. 回滚 `bustag/app/schedule.py` 与 `bustag/app/tasks.py` 可恢复同步执行路径。
2. 回滚 `bustag/app/index.py` 与 `bustag/app/views/model.tpl` 可移除任务状态接口与异步训练展示。
3. 所有改动已集中在单一分支，支持整分支回退。
