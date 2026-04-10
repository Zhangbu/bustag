# MissAV 爬取开发状态（2026-04-10）

## 当前结论

- 状态：可用原型（可在受控环境使用）
- 阶段：稳定化推进中，尚未达到“无人值守量产”

## 已完成能力

- Source adapter 已接入：`download.source=missav`
- 列表与详情 URL 生成、归一化（`missav.ws -> missav.ai`）
- 详情页解析：番号、标题、发布日期、时长、封面、标签
- Cloudflare 场景可配置：proxy/cookie/user-agent
- 单元测试覆盖：
  - `tests/test_missav.py`
  - `tests/test_spider.py`（source registry fallback）

## 本轮补强（Round 16）

- 补齐依赖声明：`curl_cffi`
  - `pyproject.toml`
  - `requirements.txt`
- Source registry 改为懒加载可选注册：
  - MissAV 依赖缺失时不影响 `bus` 运行
- 新增 MissAV 可执行探针：
  - `scripts/missav_probe.sh`
  - `make missav-probe`
- 新增探针配置：
  - `BUSTAG_MISSAV_PROBE_URL`

## 待完成项（建议优先级）

1. P0：预发/生产样本回归集
- 固定 20-50 个可公开验证样本，做 nightly 回归
- 记录解析字段完整率、失败率、重试率

2. P0：反爬稳定性观测
- 按状态码、挑战页命中率、平均重试次数出报表
- 触发阈值告警（例如 challenge 命中 > 20%）

3. P1：解析器鲁棒性增强
- 站点 DOM 变更时增加兜底规则
- 对关键字段（fanhao/release_date）做更细粒度校验

4. P1：抓取策略治理
- 增加限速和节流配置模板
- 区分全量抓取与增量抓取窗口

## 生产准入建议

同时满足以下条件再进入稳定量产：
- 连续 7 天探针成功率 >= 99%
- nightly 回归关键字段完整率 >= 98%
- challenge 命中率与重试开销处于可控范围
