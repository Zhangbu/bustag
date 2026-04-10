# Crawler-Only Runbook（不访问前端页面）

## 目标

- 线上仅运行爬虫，不启动 Web 前端服务
- 将线上爬虫产出的 `bus.db` 拉取到本地直接使用

## 前置

- 代码目录：`/home/ubuntu/bustag`
- conda 环境：`bustag`
- `.env` 已按 `.env.example` 配置

建议在 `.env` 显式配置：

```bash
BUSTAG_CONDA_ENV="bustag"
BUSTAG_CONDA_BIN="/home/ubuntu/miniconda3/bin/conda"
```

## 1. 线上仅跑一次爬虫

```bash
cd /home/ubuntu/bustag
make crawler-once
```

日志位置：
- 汇总日志：`logs/crawler_summary.log`
- 单次详细日志：`logs/crawler_*.log`

## 2. 线上循环跑爬虫（后台长期运行）

```bash
cd /home/ubuntu/bustag
nohup make crawler-loop > crawler-loop.log 2>&1 &
```

- 默认间隔：`BUSTAG_CRAWL_INTERVAL_SECONDS=3600`
- 可通过 `.env` 调整

停止：

```bash
pkill -f "scripts/crawler_loop.sh"
```

查看汇总日志：

```bash
make crawler-log-tail
```

## 3. 线上导出爬虫结果

```bash
cd /home/ubuntu/bustag
make crawler-export
```

执行后会在 `exports/` 生成：
- `busdb_*.db`
- `busdb_*.db.sha256`

## 4. 从线上拉取到本地

在本地机器执行：

```bash
scp ubuntu@<server>:/home/ubuntu/bustag/exports/busdb_*.db ./
scp ubuntu@<server>:/home/ubuntu/bustag/exports/busdb_*.db.sha256 ./
```

## 5. 本地导入线上结果

```bash
cd /home/zjxfun/forfun/bustag
make crawler-import SNAPSHOT=/absolute/path/to/busdb_YYYYMMDDTHHMMSSCST.db
```

导入逻辑：
- 若存在 `data/bus.db`，会先自动备份
- 若存在同名 `.sha256` 文件，会先做校验

## 6. 常见问题

1. `Failed to connect to 127.0.0.1:7897`
- 说明代理不可用。若不需要代理：
  - `export BUSTAG_MISSAV_PROXY=''`

2. `.env syntax error near unexpected token '('
- 说明 `.env` 里未加引号，按 `.env.example` 修复

3. 不想跑推荐模型
- 保持 `BUSTAG_CRAWL_RECOMMEND_AFTER_DOWNLOAD=0`
