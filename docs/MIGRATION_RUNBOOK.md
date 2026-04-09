# Bustag 数据库迁移发布手册

本文档用于生产/准生产环境执行 SQLite 迁移，目标是“可重复、可回滚、可核验”。

## 1. 前提

- 运行环境：WSL + conda `bustag`
- 迁移文件目录：`migrations/sql/`
- 数据库文件：`data/bus.db`
- 安全脚本：`scripts/migrate.sh`

## 2. 发布前检查

1. 确认代码版本已部署到目标环境（包含最新迁移 SQL 文件）。
2. 查看当前迁移状态：

```bash
make migrate-status
```

3. 预演待执行迁移：

```bash
make migrate-dry-run
```

4. 确认 `pending` 列表与预期一致。

## 3. 正式执行

默认使用安全脚本（启用自动备份）：

```bash
make migrate-safe
```

等价命令：

```bash
python -m bustag.main migrate --backup
```

成功后输出中应包含：

- `backup file: ...`（若数据库已存在）
- `applied: N`

## 4. 发布后验收

1. 再次检查迁移状态：

```bash
make migrate-status
```

2. 验收标准：
- `pending: 0`
- 本次发布对应迁移文件出现在 `applied` 列表中

3. 基本业务健康检查：
- `http://localhost:8000/healthz` 返回 `status=ok`
- 关键页面可访问：`/`、`/model`、`/fetch`

## 5. 回滚流程

若迁移执行过程中失败：

- 系统会自动从本次备份恢复数据库（已内置）。
- 日志会出现 `Database restored from backup`。

若迁移已成功但业务验证失败，需要手工回滚时：

1. 找到本次备份文件（输出中的 `backup file` 路径）
2. 停止应用写入
3. 用备份覆盖当前数据库：

```bash
cp /path/to/backup.bak.db data/bus.db
```

4. 重启应用并重新验收

## 6. 常见问题

1. `pending` 一直不为 0
- 检查是否部署了最新 SQL 文件
- 检查 `migrations/sql/` 文件名是否按前缀递增

2. 迁移命令报 SQL 错误
- 检查该 SQL 是否兼容当前 SQLite 版本
- 修复 SQL 后重新发布

3. 需要关闭自动备份

```bash
python -m bustag.main migrate --no-backup
```

不建议在线上使用 `--no-backup`。

## 7. 推荐执行顺序（上线模板）

```bash
make migrate-status
make migrate-dry-run
make migrate-safe
make migrate-status
```

