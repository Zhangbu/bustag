# 生产发布 Checklist（Bustag）

## 适用范围

- 目标日期：2026-04-10 之后版本
- 目标环境：WSL + conda `bustag`
- 发布策略：先灰度、后全量，始终可回滚

## 0. 发布输入

- 发布分支/commit 已冻结
- 变更日志已写入 `docs/REFACTOR_LOG.md`
- 回滚负责人和窗口已确认

## 1. 依赖与环境确认

```bash
cd /home/zjxfun/forfun/bustag
/home/zjxfun/miniconda3/bin/conda run -n bustag pip install -r requirements.txt
/home/zjxfun/miniconda3/bin/conda run -n bustag python -c "import fastapi,uvicorn,curl_cffi;print('deps ok')"
```

必须通过，否则禁止进入发布阶段。

## 2. 发布前质量门禁

```bash
/home/zjxfun/miniconda3/bin/conda run -n bustag pytest -s
```

期望：全部通过（允许已有已知 skip/warning）。

## 3. Web 双栈门禁

推荐严格模式（生产）：

```bash
export BUSTAG_GATE_ALLOW_SKIP_MISSING_FASTAPI=0
make web-release-gate
```

期望：
- Bottle 契约通过
- FastAPI 契约通过（不能 skip）

## 4. MissAV 探针（发布前）

```bash
make missav-probe
```

期望：返回 `[missav-probe] PASS ...`。

## 5. 灰度发布

1. 先将少量实例切到 FastAPI：

```bash
export BUSTAG_WEB_STACK=fastapi
# 重启服务
```

2. 验收：

```bash
make web-precheck-fastapi
```

3. 观测 30-60 分钟：
- 5xx 是否上升
- 慢请求是否异常
- `/task/*` 成功率是否正常

## 6. 扩容到全量

按 10% -> 30% -> 50% -> 100% 推进，每一步重复：

```bash
make web-precheck-fastapi
```

任何一步异常，立即执行回滚。

## 7. 回滚方案

```bash
export BUSTAG_WEB_STACK=bottle
# 重启服务
make web-precheck-bottle
```

期望：`/healthz` 的 `framework` 回到 `bottle`，契约检查通过。

## 8. 发布后归档

- 在 `docs/REFACTOR_LOG.md` 记录：时间、执行人、结果、异常、回滚情况
- 保留本次发布命令和核心输出摘要
