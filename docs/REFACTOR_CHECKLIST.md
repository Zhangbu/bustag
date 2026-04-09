# Bustag 渐进式重构清单（执行版）

## 目标

- 先稳定，再解耦，再升级技术栈。
- 每个阶段都可回滚、可验证。

## 里程碑

- [x] M1: 基线护栏（测试补齐、CI 门禁基础）
- [x] M2: 启动生命周期显式化（`create_app` + 显式 init）
- [x] M3: 生产运行现代化（gunicorn + `/healthz`）
- [ ] M4: 任务队列化（抓取/训练/推荐异步任务）
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

## 回滚策略

1. 回滚 `docker/entry.sh` 至旧启动命令可恢复原运行方式。
2. 回滚 `bustag/app/index.py` 与 `bustag/spider/db.py` 可恢复导入期初始化路径。
3. 所有改动已集中在单一分支，支持整分支回退。
