# Bustag 项目架构与代码逻辑说明

本文档基于当前仓库代码（`/home/zjxfun/forfun/bustag`）梳理项目整体架构、核心调用链、关键数据流与运行方式。

## 1. 项目定位与整体结构

Bustag 是一个“抓取数据 -> 人工打标 -> 训练模型 -> 自动推荐”的闭环系统，主要由 5 层组成：

1. Web 层（Bottle）
2. 调度层（APScheduler）
3. 爬虫层（异步 crawler + source adapter）
4. 数据层（Peewee + SQLite）
5. 模型层（scikit-learn）

核心目录：

- `bustag/app/`：Web 路由、页面交互、调度触发
- `bustag/spider/`：爬虫、路由匹配、站点解析、数据库模型
- `bustag/model/`：特征准备、训练、预测、模型持久化
- `bustag/util.py`：配置加载、路径、日志、时间工具
- `data/`：运行时数据（`config.ini`、`bus.db`、`model/*.pkl`）

## 2. 启动入口与运行模式

### 2.1 Web 入口

- 文件：`bustag/app/index.py`
- 启动方式：`python bustag/app/index.py` 或 `python -m bustag.app.index`
- 关键动作：
  - `init_app_config()` 初始化配置
  - 导入 `bustag.spider.db` 时自动建表（`db.init()`）
  - `start_scheduler()` 启动后台抓取定时任务
  - `bottle.run(..., port=8000)` 启动 Web 服务

### 2.2 CLI 入口

- 文件：`bustag/main.py`
- 命令：
  - `python -m bustag.main download`：抓取数据
  - `python -m bustag.main recommend`：基于现有模型打系统推荐分

### 2.3 你当前环境（WSL + conda bustag）

仓库已提供脚本 `scripts/start.sh`，默认会执行：

```bash
conda run -n bustag python bustag/app/index.py
```

可用方式：

```bash
# 在项目根目录
bash scripts/start.sh

# 或显式执行
conda run -n bustag python bustag/app/index.py
```

## 3. 配置与初始化机制

### 3.1 配置来源

配置加载在 `bustag/util.py`：

1. 先加载 `DEFAULT_CONFIG`
2. 再读取 `data/config.ini`
3. 最后用环境变量覆盖敏感项

关键配置项：

- `[download]`
  - `source`: 数据源（`bus` / `missav`）
  - `root_path`: 起始站点地址
  - `count`: 每次抓取上限
  - `interval`: 定时抓取间隔秒数
- `[missav]`
  - `language` / `proxy` / `browser` / `user_agent` / `cookie`
- `[auth]`
  - `admin_username` / `admin_password` / `secret_key`

环境变量覆盖：

- `BUSTAG_SECRET_KEY`
- `BUSTAG_ADMIN_PASSWORD`
- `BUSTAG_MISSAV_COOKIE`
- `BUSTAG_MISSAV_PROXY`
- `BUSTAG_MISSAV_USER_AGENT`

### 3.2 初始化顺序

`util.init()` 会：

1. 检查测试模式
2. 初始化日志
3. 加载配置
4. 确保 `data/model/` 目录存在

`bustag/spider/db.py` 在模块导入时会自动 `init()`：

1. 连接 SQLite：`data/bus.db`
2. 创建表（Item/Tag/ItemTag/ItemRate/LocalItem/User）
3. 尝试创建默认管理员（需配置密码）

## 4. Web 层逻辑（Bottle）

### 4.1 鉴权与请求钩子

文件：`bustag/app/index.py`

- 登录状态通过签名 cookie `user` 判断
- `before_request`：
  - 连接数据库
  - 鉴权拦截（`/login`、`/static` 放行）
- `after_request`：关闭数据库连接

### 4.2 主要路由

- `/`：推荐页，展示 `SYSTEM_RATE` 的喜欢/不喜欢结果
- `/tagit`：人工打标页（对样本打 `USER_RATE`）
- `/tag/<fanhao>`：提交人工打标
- `/correct/<fanhao>`：修正系统推荐结果
- `/model`：查看模型指标与可选模型
- `/do-training`：触发训练并保存模型
- `/local_fanhao`：上传番号/路径，可自动补抓缺失元数据
- `/local`：本地文件列表
- `/load_db`：导入旧数据库中的人工打标
- `/fetch`：手动按页抓取

## 5. 调度层逻辑（APScheduler）

文件：`bustag/app/schedule.py`

- `start_scheduler()` 在服务启动时注册两个任务：
  1. 1秒后先抓一次
  2. 之后按 `download.interval` 周期抓取
- 调度任务执行 `download()`：
  1. 调 `async_download_wrapper` 抓取
  2. 抓取完成后调用 `clf.recommend()` 给新样本生成系统评分

补充：`add_download_job(urls)` 支持在用户上传本地番号/导入库后，延迟追加一次抓取任务。

## 6. 爬虫层架构

### 6.1 Crawler 内核

文件：`bustag/spider/crawler.py`

核心对象：

- `Router`：URL 路由注册与路径匹配
- `Route`：单条路由规则（pattern + handler + verify）
- `Crawler`：异步并发抓取器

主要流程：

1. 从 `start_urls` 初始化队列
2. worker 并发取 URL
3. route 匹配 path
4. 抓取 HTML（默认 aiohttp，或 source 自定义 fetch）
5. 调 handler 解析保存
6. 解析并追加新链接（可由 route/no_parse_links 控制）

### 6.2 Source Adapter（可插拔站点）

目录：`bustag/spider/sources/`

- `SourceAdapter`（base）定义统一接口：
  - `build_page_urls`
  - `get_item_url`
  - `normalize_url(s)`
  - `fetch`
- `BusSourceAdapter`：bus 站点适配
- `MissAVSourceAdapter`：MissAV 适配（含 Cloudflare 场景下的 cookie/proxy 支持）

`get_source()` 根据 `download.source` 返回对应 adapter，是全局策略切换点。

### 6.3 解析器

- `bustag/spider/parser.py`：bus 页面解析
- `bustag/spider/parser_missav.py`：missav 页面解析

解析输出统一为：

- `meta`：`fanhao/title/release_date/length/cover_img_url`
- `tags`：`Tag(type, value, link)` 列表

随后由 `spider.db.save(meta, tags)` 持久化。

## 7. 数据层设计（SQLite + Peewee）

文件：`bustag/spider/db.py`

### 7.1 核心表

- `Item`：作品主表（`fanhao` 唯一）
- `Tag`：标签主表（`type + value` 唯一）
- `ItemTag`：作品-标签关联
- `ItemRate`：评分表（人工/系统）
- `LocalItem`：本地文件路径与播放统计
- `User`：登录用户（PBKDF2 密码哈希）

### 7.2 评分语义

- `RATE_TYPE`
  - `USER_RATE=1`：人工标注
  - `SYSTEM_RATE=2`：模型预测结果
- `RATE_VALUE`
  - `LIKE=1`
  - `DISLIKE=0`

### 7.3 常用查询

- `get_items(...)`：按评分条件分页查询，并预取 tags
- `get_local_items(...)`：本地文件页查询
- `get_today_update_count()`：今日新增作品
- `get_today_recommend_count()`：今日系统推荐数

## 8. 模型层逻辑（训练与推荐）

### 8.1 特征工程

文件：`bustag/model/prepare.py`

- 训练数据来源：`get_items(rate_type=USER_RATE)`
- 特征：将样本 tags 用 `MultiLabelBinarizer` one-hot
- 标签：`target = rate_value`
- 划分：`train_test_split`（尽量分层）
- 持久化：`label_binarizer.pkl`

### 8.2 模型训练

文件：`bustag/model/classifier.py`

支持模型：

- `logistic_regression`（默认）
- `knn`
- `bernoulli_nb`

训练约束：

- 最少样本 `MIN_TRAIN_NUM=200`
- 必须包含至少两类（喜欢/不喜欢）

评估指标：

- Precision / Recall / F1 / Accuracy
- TP / FP / FN / TN
- 可选交叉验证均值（cv_*）

训练产物：`data/model/model.pkl`，存 `model + scores + metadata`。

### 8.3 推荐写回

`recommend()` 流程：

1. 取“尚未评分”的样本（`rate_type is null`）
2. 用已保存的 binarizer 做特征转换
3. 模型预测 `0/1`
4. 每条预测写入 `ItemRate(rate_type=SYSTEM_RATE)`

## 9. 端到端业务闭环

### 9.1 自动闭环

1. 定时抓取新数据
2. 用户在 `/tagit` 人工打标
3. 在 `/do-training` 训练模型
4. 定时任务或手动抓取后自动执行 recommend
5. `/` 页面展示系统推荐
6. 用户可在 `/correct` 回写修正，进入新一轮训练

### 9.2 本地文件闭环

1. `/local_fanhao` 上传番号（可附带路径）
2. 缺失元数据的番号会进入 `add_download_job`
3. 补抓后进入统一 Item/Tag 体系
4. 可参与训练与推荐

## 10. 你后续维护最需要关注的点

1. `download.source` 是站点策略开关，扩展新站点优先走 adapter 模式。
2. `ItemRate` 是系统行为核心：人工与系统评分都汇聚于此。
3. 训练前务必保证人工样本数和类别分布达标。
4. MissAV 抓取稳定性与 `proxy/cookie/user_agent` 强相关。
5. 数据目录是状态中心：`data/config.ini`、`data/bus.db`、`data/model/*.pkl`。

## 11. 建议的本地运行检查清单（WSL + conda bustag）

```bash
# 1) 确认环境
conda run -n bustag python --version

# 2) 安装依赖（首次）
conda run -n bustag pip install -e .

# 3) 启动服务
bash scripts/start.sh

# 4) 访问
# http://localhost:8000
```

如果服务启动后不能登录，请先检查：

- `data/config.ini` 是否配置了 `[auth] admin_password`
- 或是否设置了 `BUSTAG_ADMIN_PASSWORD` 环境变量

---

以上内容对应当前代码实现，不是理想化设计图；后续如果你改动了 source adapter、评分逻辑或模型输入特征，这份文档建议同步更新。
