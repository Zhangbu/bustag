# Bustag 开发文档

> 本文档为 Bustag 项目的完整开发指南，供开发者了解项目架构、进行功能开发和维护。

## 目录

1. [项目概述](#1-项目概述)
2. [系统架构](#2-系统架构)
3. [目录结构](#3-目录结构)
4. [核心模块详解](#4-核心模块详解)
5. [数据模型](#5-数据模型)
6. [API路由](#6-api路由)
7. [配置系统](#7-配置系统)
8. [开发环境配置](#8-开发环境配置)
9. [开发规范](#9-开发规范)
10. [功能开发指南](#10-功能开发指南)
11. [常见任务清单](#11-常见任务清单)
12. [调试与故障排除](#12-调试与故障排除)

---

## 1. 项目概述

### 1.1 项目简介

**Bustag** 是一个基于机器学习的车牌自动推荐系统。系统通过定时爬取最新车牌信息，允许用户对车牌进行打标（标示是否喜欢），当打标数据积累到一定数量后可以训练模型，之后系统可以自动预测并推荐用户可能喜欢的车牌。

### 1.2 核心功能

| 功能 | 描述 |
|------|------|
| 自动爬取 | 定时从目标网站爬取最新车牌信息 |
| 打标功能 | 用户可以标记喜欢/不喜欢 |
| 模型训练 | 基于打标数据训练 KNN 分类模型 |
| 自动推荐 | 使用训练好的模型预测并推荐 |
| 本地管理 | 本地文件管理和番号上传 |
| 数据导入 | 支持从数据库文件导入打标数据 |

### 1.3 技术栈

| 组件 | 版本 | 用途 |
|------|------|------|
| Python | 3.10+ | 运行环境 |
| Bottle | 0.13+ | Web 框架 |
| aiohttp | 3.9+ | 异步 HTTP 客户端（爬虫） |
| Peewee | 3.17+ | ORM |
| scikit-learn | 1.5+ | 机器学习 |
| pandas | 2.2+ | 数据处理 |
| APScheduler | 3.10+ | 定时任务 |
| SQLite | - | 数据库 |

### 1.4 项目版本

当前版本：`0.3.0`

---

## 2. 系统架构

### 2.1 整体架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                         Web Layer (Bottle)                       │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐  │
│  │  推荐   │ │  打标   │ │  本地   │ │  模型   │ │  数据   │  │
│  │  页面   │ │  页面   │ │  页面   │ │  页面   │ │  页面   │  │
│  └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘  │
└───────┼──────────┼──────────┼──────────┼──────────┼───────────┘
        │          │          │          │          │
┌───────┴──────────┴──────────┴──────────┴──────────┴───────────┐
│                       Business Logic Layer                     │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐  │
│  │   Spider 模块    │  │    Model 模块   │  │   App 模块   │  │
│  │  - crawler      │  │  - classifier   │  │  - schedule  │  │
│  │  - parser       │  │  - prepare      │  │  - local     │  │
│  │  - bus_spider   │  │  - persist      │  │              │  │
│  │  - db           │  │                 │  │              │  │
│  └────────┬────────┘  └────────┬────────┘  └──────┬───────┘  │
└───────────┼────────────────────┼──────────────────┼───────────┘
            │                    │                  │
┌───────────┴────────────────────┴──────────────────┴───────────┐
│                       Data Layer                               │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐  │
│  │   SQLite DB     │  │   Model Files   │  │  Config File │  │
│  │   (bus.db)      │  │   (model.pkl)   │  │  (config.ini)│  │
│  └─────────────────┘  └─────────────────┘  └──────────────┘  │
└───────────────────────────────────────────────────────────────┘
```

### 2.2 数据流图

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   目标网站    │────▶│   Crawler    │────▶│    Parser    │
└──────────────┘     │  (aiohttp)   │     │ (HTML解析)   │
                     └──────────────┘     └──────┬───────┘
                                                 │
                                                 ▼
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  用户打标    │────▶│   ItemRate   │◀────│    Item      │
│  (Web UI)    │     │   (评分表)    │     │   (车牌表)   │
└──────────────┘     └──────┬───────┘     └──────────────┘
                            │
                            ▼
                     ┌──────────────┐
                     │ Prepare Data │
                     │  (特征提取)  │
                     └──────┬───────┘
                            │
                            ▼
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  模型训练    │────▶│ KNeighbors   │────▶│  model.pkl   │
│  (train)     │     │ Classifier   │     │              │
└──────────────┘     └──────┬───────┘     └──────────────┘
                            │
                            ▼
┌──────────────┐     ┌──────────────┐
│  自动推荐    │────▶│ 预测结果     │
│  (recommend) │     │ (新ItemRate) │
└──────────────┘     └──────────────┘
```

### 2.3 模块依赖关系

```
bustag/
├── __init__.py          # 版本信息
├── main.py              # CLI 入口 ──┐
├── util.py              # 工具函数 ◀─┤
│                          │
├── spider/              # 爬虫模块 ──┤
│   ├── __init__.py      #            │
│   ├── db.py            # ◀──────────┼── 数据模型定义
│   ├── crawler.py       # ◀──────────┼── 异步爬虫
│   ├── parser.py        # ◀──────────┼── HTML 解析
│   └── bus_spider.py    # ◀──────────┘── 路由处理
│
├── model/               # 机器学习模块
│   ├── __init__.py
│   ├── classifier.py    # ◀── 分类器
│   ├── prepare.py       # ◀── 数据准备
│   └── persist.py        # ◀── 模型持久化
│
└── app/                  # Web 应用模块
    ├── __init__.py
    ├── index.py          # ◀── Web 路由
    ├── schedule.py       # ◀── 定时任务
    ├── local.py          # ◀── 本地文件处理
    ├── static/           # ◀── 静态资源
    └── views/            # ◀── 模板文件
```

---

## 3. 目录结构

```
bustag/
├── bustag/                    # 主包目录
│   ├── __init__.py           # 包初始化，版本信息
│   ├── main.py               # CLI 命令入口 (download, recommend)
│   ├── util.py               # 工具函数 (配置、日志、路径)
│   │
│   ├── spider/               # 爬虫子包
│   │   ├── __init__.py
│   │   ├── db.py             # 数据库模型 (Item, Tag, ItemRate, LocalItem)
│   │   ├── crawler.py        # 异步爬虫 (Router, Crawler)
│   │   ├── parser.py         # HTML 解析器
│   │   └── bus_spider.py     # 业务路由处理
│   │
│   ├── model/                # 机器学习子包
│   │   ├── __init__.py
│   │   ├── classifier.py     # 分类器 (KNN, 训练, 预测)
│   │   ├── prepare.py       # 数据准备 (特征提取)
│   │   └── persist.py        # 模型持久化
│   │
│   └── app/                  # Web 应用子包
│       ├── __init__.py
│       ├── index.py          # Bottle 应用入口，路由定义
│       ├── schedule.py       # APScheduler 定时任务
│       ├── local.py          # 本地文件处理
│       ├── static/           # 静态资源
│       │   ├── css/          # 样式文件
│       │   ├── js/           # JavaScript
│       │   └── images/       # 图片资源
│       └── views/            # Bottle 模板
│           ├── base.tpl      # 基础模板
│           ├── index.tpl     # 推荐页面
│           ├── tagit.tpl     # 打标页面
│           ├── local.tpl     # 本地页面
│           ├── local_fanhao.tpl
│           ├── load_db.tpl   # 数据导入页面
│           ├── model.tpl     # 模型页面
│           ├── about.tpl     # 关于页面
│           └── pagination.tpl
│
├── data/                     # 数据目录
│   ├── config.ini           # 配置文件 (必须)
│   ├── bus.db               # SQLite 数据库 (自动生成)
│   └── model/               # 模型目录 (自动生成)
│       ├── model.pkl        # 训练好的模型
│       └── label_binarizer.pkl  # 标签二值化器
│
├── tests/                    # 测试目录
│   ├── conftest.py          # pytest 配置
│   ├── test_db.py           # 数据库测试
│   ├── test_main.py         # 主入口测试
│   ├── test_model.py        # 模型测试
│   ├── test_parser.py       # 解析器测试
│   ├── test_persist.py      # 持久化测试
│   ├── test_prepare.py      # 数据准备测试
│   ├── test_spider.py       # 爬虫测试
│   └── test_util.py         # 工具函数测试
│
├── docker/                   # Docker 相关
│   ├── crontab.txt          # 定时任务配置
│   ├── entry.sh             # 容器入口脚本
│   ├── run_download.sh      # 下载脚本
│   └── sources.list         # apt 源配置
│
├── docs/                     # 文档截图
├── pyproject.toml           # 项目配置 (PEP 517/518)
├── requirements.txt         # 依赖列表
├── requirements-dev.txt     # 开发依赖
├── setup.py                 # 传统安装脚本
├── Dockerfile               # Docker 构建文件
├── Makefile                 # Make 命令
├── tox.ini                  # tox 配置
└── README.md                # 项目说明
```

---

## 4. 核心模块详解

### 4.1 Spider 模块 (爬虫)

#### 4.1.1 crawler.py - 异步爬虫

**核心类：**

```python
class Router:
    """URL 路由器，管理 URL 匹配和处理"""
    - routes: list[Route]      # 路由列表
    - base_url: str            # 基础 URL
    + route(pattern, verify_func, no_parse_links)  # 路由装饰器
    + get_url_path(url)        # 提取 URL 路径
    + set_base_url(url)        # 设置基础 URL

class Route:
    """路由定义"""
    - pattern: str             # 路由模式
    - handler: Callable        # 处理函数
    - verify_func: Callable    # 验证函数
    - no_parse_links: bool    # 是否解析链接
    + match(path)              # 匹配路径

class Crawler:
    """异步爬虫"""
    - router: Router           # 路由器
    - max_count: int          # 最大爬取数
    - seen_urls: set          # 已处理 URL
    - urls_to_process: list   # 待处理 URL
    + crawl(start_urls)       # 开始爬取
```

**使用示例：**

```python
from bustag.spider.crawler import get_router, async_download
import asyncio

# 获取全局路由器
router = get_router()

# 注册路由处理
@router.route(r'/<fanhao:[\w]+-[\d]+>', verify_fanhao, no_parse_links=True)
def process_item(text, path, fanhao):
    # 处理详情页
    pass

# 启动爬虫
router.set_base_url('https://example.com')
asyncio.run(async_download(['https://example.com'], count=100))
```

#### 4.1.2 parser.py - HTML 解析

```python
def parse_item(text: str) -> tuple[dict, list]:
    """
    解析项目详情页
    
    Args:
        text: HTML 文本
        
    Returns:
        (meta, tags) - 元数据字典和标签列表
    """
    # 提取: fanhao, title, cover_img_url, release_date, length
    # 标签类型: genre, star
```

#### 4.1.3 db.py - 数据库模型

**数据表定义：**

| 表名 | 说明 |
|------|------|
| `Item` | 车牌信息 |
| `Tag` | 标签 |
| `ItemTag` | 车牌-标签关联 |
| `ItemRate` | 评分记录 |
| `LocalItem` | 本地文件记录 |

**初始化：**

```python
from bustag.spider.db import init, db
init()  # 初始化数据库连接和表创建
```

### 4.2 Model 模块 (机器学习)

#### 4.2.1 classifier.py - 分类器

```python
# 核心函数
def train() -> tuple:
    """训练模型，返回 (model, scores)"""
    
def predict(X_test) -> np.ndarray:
    """使用模型预测"""
    
def recommend():
    """对所有未评分项目进行预测推荐"""

def create_model():
    """创建 KNN 分类器 (n_neighbors=11)"""
    
def load():
    """加载模型"""
    
def evaluate(confusion_mtx, y_test, y_pred) -> dict:
    """评估模型，返回 precision, recall, f1"""
```

**模型参数：**
- 算法：KNeighborsClassifier
- n_neighbors: 11
- 最小训练数据：200 条

#### 4.2.2 prepare.py - 数据准备

```python
def prepare_data() -> tuple:
    """
    准备训练数据
    
    Returns:
        (X_train, X_test, y_train, y_test)
    """
    
def prepare_predict_data() -> tuple:
    """
    准备预测数据
    
    Returns:
        (ids, X) - ID 数组和特征矩阵
    """
    
def load_data() -> list:
    """加载已评分数据"""
    
def process_data(df) -> tuple:
    """处理数据，使用 MultiLabelBinarizer 进行特征编码"""
```

**特征工程：**
- 使用 MultiLabelBinarizer 对标签进行二值化编码
- 训练/测试集划分比例：75%/25%
- random_state: 42

### 4.3 App 模块 (Web 应用)

#### 4.3.1 index.py - Web 路由

**路由列表：**

| 路由 | 方法 | 功能 |
|------|------|------|
| `/` | GET | 推荐页面 |
| `/tagit` | GET | 打标页面 |
| `/tag/<fanhao>` | POST | 提交打标 |
| `/correct/<fanhao>` | POST | 纠正评分 |
| `/model` | GET | 模型页面 |
| `/do-training` | GET | 执行训练 |
| `/local` | GET | 本地文件页面 |
| `/local_fanhao` | GET/POST | 上传番号 |
| `/local_play/<id>` | GET | 播放本地文件 |
| `/load_db` | GET/POST | 导入数据库 |
| `/about` | GET | 关于页面 |
| `/static/<filepath>` | GET | 静态文件 |

**启动方式：**

```python
# 方式1：直接运行
python bustag/app/index.py

# 方式2：gunicorn
gunicorn bustag.app.index:app --bind='0.0.0.0:8000'
```

#### 4.3.2 schedule.py - 定时任务

```python
def start_scheduler():
    """
    启动定时任务调度器
    
    - 启动后 1 秒执行一次下载
    - 按 interval 配置周期执行下载
    - 下载完成后自动执行推荐
    """

def add_download_job(urls):
    """添加下载任务（10秒后执行）"""

def download(loop, no_parse_links, urls):
    """下载并推荐"""
```

#### 4.3.3 local.py - 本地文件处理

```python
def add_local_fanhao(fanhao, tag_like) -> tuple:
    """
    添加本地番号
    
    Args:
        fanhao: 番号列表（每行一个，可带路径）
        tag_like: 是否标记为喜欢
        
    Returns:
        (missed_fanhaos, local_file_count, tag_file_count)
    """

def load_tags_db() -> tuple:
    """
    从上传的数据库加载打标数据
    
    Returns:
        (tag_file_added, missed_fanhaos)
    """
```

---

## 5. 数据模型

### 5.1 表结构

#### Item 表（车牌信息）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键 |
| title | VARCHAR | 标题 |
| fanhao | VARCHAR | 番号（唯一） |
| url | VARCHAR | URL（唯一） |
| release_date | DATE | 发布日期 |
| add_date | DATETIME | 添加时间 |
| meta_info | TEXT | JSON 元数据 |

#### Tag 表（标签）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键 |
| type_ | VARCHAR | 标签类型 (genre/star) |
| value | VARCHAR | 标签值 |
| url | VARCHAR | 标签链接 |

#### ItemTag 表（关联表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键 |
| item | VARCHAR | 外键 → Item.fanhao |
| tag | INTEGER | 外键 → Tag.id |

#### ItemRate 表（评分记录）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键 |
| rate_type | INTEGER | 评分类型（0:未评分, 1:用户, 2:系统） |
| rate_value | INTEGER | 评分值（0:不喜欢, 1:喜欢） |
| item | VARCHAR | 外键 → Item.fanhao（唯一） |
| rete_time | DATETIME | 评分时间 |

#### LocalItem 表（本地文件）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键 |
| item | VARCHAR | 外键 → Item.fanhao（唯一） |
| path | VARCHAR | 文件路径 |
| size | INTEGER | 文件大小 |
| add_date | DATETIME | 添加时间 |
| last_view_date | DATETIME | 最后播放时间 |
| view_times | INTEGER | 播放次数 |

### 5.2 枚举类型

```python
class RATE_TYPE(IntEnum):
    NOT_RATE = 0      # 未评分
    USER_RATE = 1    # 用户评分
    SYSTEM_RATE = 2   # 系统预测

class RATE_VALUE(IntEnum):
    LIKE = 1          # 喜欢
    DISLIKE = 0       # 不喜欢
```

---

## 6. API路由

### 6.1 页面路由

| 路由 | 方法 | 参数 | 说明 |
|------|------|------|------|
| `/` | GET | `like`, `page` | 推荐列表页面 |
| `/tagit` | GET | `like`, `page` | 打标页面 |
| `/model` | GET | - | 模型管理页面 |
| `/local` | GET | `page` | 本地文件页面 |
| `/local_fanhao` | GET/POST | `fanhao`, `tag_like` | 番号上传 |
| `/load_db` | GET/POST | `dbfile` | 数据库导入 |
| `/about` | GET | - | 关于页面 |

### 6.2 操作路由

| 路由 | 方法 | 参数 | 说明 |
|------|------|------|------|
| `/tag/<fanhao>` | POST | `submit`, `formid` | 提交打标 |
| `/correct/<fanhao>` | POST | `submit`, `formid` | 纠正评分 |
| `/do-training` | GET | - | 执行模型训练 |
| `/local_play/<id>` | GET | - | 播放本地文件 |

### 6.3 静态资源

| 路由 | 说明 |
|------|------|
| `/static/css/*` | CSS 样式文件 |
| `/static/js/*` | JavaScript 文件 |
| `/static/images/*` | 图片资源 |

---

## 7. 配置系统

### 7.1 配置文件 (data/config.ini)

```ini
[download]
root_path = https://www.busdmm.work    # 爬虫起始地址
count = 100                            # 每次下载数量
interval = 10800                       # 下载间隔（秒）
```

### 7.2 配置加载流程

```python
# bustag/util.py
def load_config():
    """
    1. 检查配置文件是否存在
    2. 读取默认配置
    3. 读取用户配置覆盖默认值
    4. 存入 APP_CONFIG 字典
    """
    
# 配置访问方式
APP_CONFIG['download.root_path']  # 爬虫地址
APP_CONFIG['download.count']      # 下载数量
APP_CONFIG['download.interval']   # 下载间隔
```

### 7.3 默认配置

```python
DEFAULT_CONFIG = {
    'download': {
        'count': 100,      # 默认下载 100 条
        'interval': 3600   # 默认间隔 1 小时
    }
}
```

---

## 8. 开发环境配置

### 8.1 环境要求

- Python 3.10+ (支持 3.10, 3.11, 3.12, 3.13)
- pip 或 uv 包管理器

### 8.2 安装步骤

```bash
# 1. 克隆项目
git clone https://github.com/gxtrobot/bustag.git
cd bustag

# 2. 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate   # Windows

# 3. 安装依赖
pip install -e ".[dev]"    # 安装开发依赖
# 或
pip install -e .           # 仅安装运行依赖

# 4. 创建配置文件
mkdir -p data
cat > data/config.ini << 'EOF'
[download]
root_path = https://www.busdmm.work
count = 100
interval = 10800
EOF

# 5. 运行项目
python bustag/app/index.py

# 或使用 gunicorn
gunicorn bustag.app.index:app --bind='0.0.0.0:8000'
```

### 8.3 运行测试

```bash
# 运行所有测试
pytest

# 运行特定测试
pytest tests/test_model.py -v

# 带覆盖率报告
pytest --cov=bustag

# 代码格式化
ruff format .

# 类型检查
mypy bustag
```

### 8.4 Docker 开发

```bash
# 构建镜像
docker build -t bustag-app .

# 运行容器
docker run --rm -d \
  --name bustag \
  -e TZ=Asia/Shanghai \
  -v $(pwd)/data:/app/data \
  -p 8000:8000 \
  bustag-app
```

---

## 9. 开发规范

### 9.1 代码风格

- **格式化工具**: ruff
- **行长度**: 120 字符
- **Python 版本**: 3.10+

```toml
# pyproject.toml
[tool.ruff]
line-length = 120
target-version = "py310"

[tool.ruff.lint]
select = ["E", "F", "W", "I", "N", "UP", "B", "C4"]
ignore = ["E501"]
```

### 9.2 命名约定

| 类型 | 约定 | 示例 |
|------|------|------|
| 模块 | 小写下划线 | `bus_spider.py` |
| 类 | 大驼峰 | `ItemRate`, `LocalItem` |
| 函数 | 小写下划线 | `get_items()`, `load_config()` |
| 变量 | 小写下划线 | `item_list`, `total_count` |
| 常量 | 大写下划线 | `MIN_TRAIN_NUM`, `MODEL_FILE` |
| 私有方法 | 前置下划线 | `_connect_db()`, `_remove_extra_tags()` |

### 9.3 类型注解

```python
# 推荐使用类型注解
from typing import Optional, Callable

def get_items(
    rate_type: Optional[int] = None,
    rate_value: Optional[int] = None,
    page: int = 1,
    page_size: int = 10
) -> tuple[list, tuple]:
    ...
```

### 9.4 文档字符串

```python
def add_local_fanhao(fanhao: str, tag_like: bool) -> tuple:
    '''
    添加本地番号
    
    Args:
        fanhao: 番号列表，逗号分隔，可带路径
        tag_like: 是否标记为喜欢
        
    Returns:
        tuple: (missed_fanhaos, local_file_count, tag_file_count)
    '''
```

---

## 10. 功能开发指南

### 10.1 添加新的 Web 路由

**步骤：**

1. 在 `bustag/app/index.py` 中添加路由处理函数：

```python
@route('/new-feature')
def new_feature():
    """新功能页面"""
    # 获取数据
    items, page_info = get_items(...)
    # 返回模板
    return template('new_feature', items=items, path=request.path)
```

2. 在 `bustag/app/views/` 中创建模板文件 `new_feature.tpl`：

```html
% rebase('base.tpl', title='新功能', path=path)

<div class="container">
  <!-- 页面内容 -->
</div>
```

3. 在 `base.tpl` 的导航栏添加链接：

```html
<li class="nav-item {{ 'active' if path=='/new-feature' else ''}}">
  <a class="nav-link" href="/new-feature">新功能</a>
</li>
```

### 10.2 添加新的爬虫路由

**步骤：**

1. 在 `bustag/spider/bus_spider.py` 中添加路由处理：

```python
@router.route('/new-path/<param>', verify_function)
def process_new_path(text, path, param):
    """
    处理新的 URL 路径
    
    Args:
        text: HTML 文本
        path: URL 路径
        param: 提取的参数
    """
    # 解析数据
    # 保存到数据库
    pass
```

2. 如需验证函数：

```python
def verify_function(path, param):
    """验证是否应该处理此 URL"""
    # 返回 True 处理，返回 False 跳过
    return True
```

### 10.3 添加新的数据模型

**步骤：**

1. 在 `bustag/spider/db.py` 中定义模型：

```python
class NewModel(BaseModel):
    """新模型说明"""
    field1 = CharField()
    field2 = IntegerField()
    add_date = DateTimeField(default=datetime.datetime.now)

    class Meta:
        indexes = (
            (('field1', 'field2'), True),  # 联合唯一索引
        )
```

2. 在 `init()` 函数中添加表创建：

```python
def init():
    db.connect(reuse_if_open=True)
    db.create_tables([Item, Tag, ItemTag, ItemRate, LocalItem, NewModel])
```

### 10.4 扩展机器学习模型

**步骤：**

1. 在 `bustag/model/classifier.py` 中修改 `create_model()`：

```python
def create_model():
    """创建分类模型"""
    from sklearn.ensemble import RandomForestClassifier
    # 使用不同的模型
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    return model
```

2. 或添加模型选择逻辑：

```python
def create_model(model_type='knn'):
    """创建分类模型"""
    if model_type == 'knn':
        return KNeighborsClassifier(n_neighbors=11)
    elif model_type == 'rf':
        return RandomForestClassifier(n_estimators=100)
    elif model_type == 'svm':
        return SVC(kernel='rbf', probability=True)
```

### 10.5 添加定时任务

**步骤：**

1. 在 `bustag/app/schedule.py` 中添加任务函数：

```python
def my_scheduled_task():
    """定时任务说明"""
    # 任务逻辑
    pass
```

2. 在 `start_scheduler()` 中注册任务：

```python
def start_scheduler():
    global scheduler
    scheduler = AsyncIOScheduler()
    
    # 添加定时任务
    scheduler.add_job(
        my_scheduled_task, 
        trigger=IntervalTrigger(hours=1),
        id='my_task'
    )
    
    scheduler.start()
```

---

## 11. 常见任务清单

### 11.1 添加新的页面

- [ ] 在 `bustag/app/index.py` 添加路由
- [ ] 在 `bustag/app/views/` 创建模板
- [ ] 在 `base.tpl` 添加导航链接
- [ ] 添加相应的 CSS/JS（如需要）

### 11.2 添加新的 API 接口

- [ ] 在 `bustag/app/index.py` 添加路由
- [ ] 定义请求/响应格式
- [ ] 添加错误处理
- [ ] 编写测试用例

### 11.3 修改爬虫逻辑

- [ ] 分析目标网站结构
- [ ] 在 `parser.py` 添加/修改解析函数
- [ ] 在 `bus_spider.py` 添加路由处理
- [ ] 测试爬虫功能

### 11.4 修改模型特征

- [ ] 分析当前特征效果
- [ ] 在 `prepare.py` 修改特征提取
- [ ] 重新训练模型
- [ ] 评估新模型效果

### 11.5 修改数据库结构

- [ ] 在 `db.py` 修改模型定义
- [ ] 考虑数据迁移策略
- [ ] 更新相关查询函数
- [ ] 更新测试用例

---

## 12. 调试与故障排除

### 12.1 启用调试日志

```python
# 设置环境变量
import os
os.environ['TESTING'] = 'true'

# 或在代码中
from bustag.util import logger
logger.setLevel(logging.DEBUG)
```

### 12.2 常见问题

#### 问题 1: 配置文件不存在

```
错误信息: file .../config.ini not exists
解决方案: 在 data/ 目录创建 config.ini 文件
```

#### 问题 2: 模型文件未找到

```
错误信息: FileNotFoundError: model.pkl
解决方案: 访问 /model 页面点击"训练模型"
原因: 需要至少 200 条打标数据才能训练
```

#### 问题 3: 数据库连接错误

```
错误信息: peewee.OperationalError
解决方案: 检查 data/bus.db 文件权限
```

#### 问题 4: 爬虫无法获取数据

```
可能原因:
1. 目标网站不可访问
2. 网站结构已变化
3. 需要代理访问

调试方法:
1. 检查 root_path 配置
2. 查看爬虫日志
3. 手动测试 URL 访问
```

### 12.3 数据库调试

```python
# 直接查询数据库
from bustag.spider.db import Item, ItemRate, db

# 查看所有表
print(db.get_tables())

# 统计数据
print(f'总条目: {Item.select().count()}')
print(f'已打标: {ItemRate.select().count()}')

# 查看最近数据
for item in Item.select().order_by(Item.id.desc()).limit(5):
    print(item.fanhao, item.title)
```

### 12.4 模型调试

```python
from bustag.model.classifier import load, train
from bustag.model.prepare import load_data

# 查看训练数据
items = load_data()
print(f'训练数据量: {len(items)}')

# 查看模型评分
model, scores = load()
print(f'模型评分: {scores}')

# 重新训练
try:
    model, scores = train()
    print(f'新模型评分: {scores}')
except ValueError as e:
    print(f'训练失败: {e}')
```

---

## 附录

### A. 项目依赖

```
# 核心依赖
bottle>=0.13.2          # Web 框架
gunicorn>=22.0.0        # WSGI 服务器
peewee>=3.17.1          # ORM

# 爬虫
aiohttp>=3.9.5          # 异步 HTTP
requests>=2.32.3        # HTTP 客户端
requests-html>=0.10.0   # HTML 解析
beautifulsoup4>=4.12.3  # HTML 解析
lxml>=5.2.2             # XML 解析

# 机器学习
scikit-learn>=1.5.0     # ML 框架
pandas>=2.2.2           # 数据处理
numpy>=1.26.4           # 数值计算

# 调度
APScheduler>=3.10.4     # 定时任务

# 开发依赖
pytest>=8.2.0           # 测试框架
ruff>=0.4.4             # 格式化
mypy>=1.10.0            # 类型检查
```

### B. 快速命令参考

```bash
# 开发
pip install -e ".[dev]"  # 安装开发依赖
pytest                   # 运行测试
ruff format .           # 格式化代码
mypy bustag             # 类型检查

# 运行
python bustag/app/index.py           # 启动 Web 服务
bustag download --count 50           # CLI 下载
bustag recommend                     # CLI 推荐

# Docker
docker build -t bustag-app .                        # 构建镜像
docker run -d -p 8000:8000 -v $(pwd)/data:/app/data bustag-app  # 运行容器
```

### C. 相关链接

- **项目仓库**: https://github.com/gxtrobot/bustag
- **问题反馈**: https://github.com/gxtrobot/bustag/issues
- **Python in Action**: https://github.com/gxtrobot/pyinaction

---

## 13. 关键代码模式

### 13.1 数据库操作模式

```python
# 创建记录
item = Item.create(fanhao='ABC-123', title='Title', url='url', ...)

# 查询单条
item = Item.get_by_id(id)
item = Item.get_or_none(Item.fanhao == 'ABC-123')

# 批量查询
items = Item.select().where(Item.add_date > date).order_by(Item.id.desc())

# 关联查询（使用 prefetch 优化）
from peewee import prefetch
items = prefetch(Item.select(), ItemTag.select(), Tag.select())

# 事务操作
with db.atomic():
    for item in items:
        item.save()

# 更新记录
nrows = Item.update({Item.field: value}).where(Item.id == id).execute()
```

### 13.2 路由处理模式

```python
# 标准页面路由
@route('/path')
def page_handler():
    page = int(request.query.get('page', 1))
    items, page_info = get_items(page=page)
    return template('template_name', items=items, page_info=page_info, path=request.path)

# 表单处理路由
@route('/action/<id>', method='POST')
def action_handler(id):
    if request.POST.submit:
        # 处理表单
        pass
    redirect(f'/page?page={page}')

# 带参数的路由
@route('/item/<fanhao>')
def item_handler(fanhao):
    item = Item.get_by_fanhao(fanhao)
    return template('item', item=item)
```

### 13.3 爬虫处理模式

```python
from bustag.spider.crawler import get_router
from bustag.spider.parser import parse_item
from bustag.spider.db import save

router = get_router()

# 定义验证函数
def verify_item(path, fanhao):
    """检查是否应该处理此项目"""
    exists = Item.get_by_fanhao(fanhao)
    return exists is None  # 不存在才处理

# 注册路由
@router.route(r'/<fanhao:[\w]+-[\d]+>', verify_item, no_parse_links=True)
def process_item(text, path, fanhao):
    """处理详情页"""
    meta, tags = parse_item(text)
    meta.update(url=path)
    save(meta, tags)
    print(f'processed: {fanhao}')
```

### 13.4 异步任务模式

```python
import asyncio
from bustag.spider.crawler import async_download, get_router

async def async_task():
    """异步任务"""
    router = get_router()
    router.set_base_url('https://example.com')
    await async_download(['https://example.com'], count=100)

# 同步调用异步任务
asyncio.run(async_task())
```

### 13.5 模板继承模式

```html
<!-- 子模板 -->
% rebase('base.tpl', title='页面标题', path=path, msg=msg)

<div class="container">
  <!-- 页面内容 -->
</div>

<!-- 包含分页组件 -->
% include('pagination.tpl', page_info=page_info)
```

---

## 14. 系统扩展点

### 14.1 爬虫扩展点

| 扩展点 | 文件位置 | 扩展方式 |
|--------|----------|----------|
| 新增 URL 模式 | `bus_spider.py` | 添加 `@router.route()` 装饰器 |
| 修改解析逻辑 | `parser.py` | 修改或新增 `parse_*` 函数 |
| 自定义验证 | `bus_spider.py` | 添加 `verify_*` 函数 |
| 新增数据存储 | `db.py` | 添加新的 Model 类 |

### 14.2 模型扩展点

| 扩展点 | 文件位置 | 扩展方式 |
|--------|----------|----------|
| 更换分类器 | `classifier.py` | 修改 `create_model()` 函数 |
| 添加特征 | `prepare.py` | 修改 `process_data()` 函数 |
| 自定义评估 | `classifier.py` | 修改 `evaluate()` 函数 |

### 14.3 Web 扩展点

| 扩展点 | 文件位置 | 扩展方式 |
|--------|----------|----------|
| 新增页面 | `index.py` | 添加 `@route()` 装饰器 |
| 新增模板 | `views/` | 创建 `.tpl` 文件 |
| 新增静态资源 | `static/` | 添加 CSS/JS/图片 |
| 新增定时任务 | `schedule.py` | 在 `start_scheduler()` 中添加 |

### 14.4 扩展示例：添加新的分类模型

```python
# 在 classifier.py 中添加
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC

MODEL_TYPES = {
    'knn': lambda: KNeighborsClassifier(n_neighbors=11),
    'rf': lambda: RandomForestClassifier(n_estimators=100, random_state=42),
    'svm': lambda: SVC(kernel='rbf', probability=True, random_state=42),
}

def create_model(model_type='knn'):
    """创建指定类型的分类模型"""
    if model_type in MODEL_TYPES:
        return MODEL_TYPES[model_type]()
    raise ValueError(f'Unknown model type: {model_type}')

def train(model_type='knn'):
    """使用指定模型训练"""
    model = create_model(model_type)
    # ... 训练逻辑
```

---

## 15. 数据验证规则

### 15.1 番号格式验证

```python
import re

FANHAO_PATTERN = r'^[A-Z]+-?\d+$'  # 如: ABC-123, ABC123

def validate_fanhao(fanhao: str) -> bool:
    """验证番号格式"""
    if not fanhao:
        return False
    fanhao = fanhao.strip().upper()
    return bool(re.match(FANHAO_PATTERN, fanhao))

def normalize_fanhao(fanhao: str) -> str:
    """标准化番号格式"""
    pattern = r'([A-Z]+)-?([0-9]+)'
    match = re.search(pattern, fanhao.upper())
    if match:
        series, num = match.groups()
        return f'{series}-{num}'
    return fanhao
```

### 15.2 URL 验证

```python
from urllib.parse import urlparse

def validate_url(url: str) -> bool:
    """验证 URL 格式"""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False
```

### 15.3 配置验证

```python
def validate_config(config: dict) -> list[str]:
    """验证配置，返回错误列表"""
    errors = []
    
    if not config.get('download.root_path'):
        errors.append('缺少 download.root_path 配置')
    
    count = config.get('download.count', 100)
    if not isinstance(count, int) or count < 1 or count > 1000:
        errors.append('download.count 应为 1-1000 之间的整数')
    
    interval = config.get('download.interval', 1800)
    if not isinstance(interval, int) or interval < 300:
        errors.append('download.interval 应为不小于 300 的整数（秒）')
    
    return errors
```

---

## 16. 系统异常定义

### 16.1 自定义异常

```python
# 在 bustag/spider/db.py 中定义
class ExistError(Exception):
    """记录已存在异常"""
    pass

class DBError(Exception):
    """数据库操作异常"""
    pass

# 使用示例
try:
    item = Item.saveit(meta_info)
except ExistError:
    logger.debug(f'Item already exists: {meta_info["fanhao"]}')
```

### 16.2 异常处理模式

```python
# 数据库操作
try:
    with db.atomic():
        # 数据库操作
        pass
except IntegrityError as e:
    logger.error(f'数据完整性错误: {e}')
except DatabaseError as e:
    logger.error(f'数据库错误: {e}')

# 模型训练
try:
    model, scores = clf.train()
except ValueError as e:
    # 训练数据不足
    error_msg = str(e)
except FileNotFoundError as e:
    # 模型文件不存在
    error_msg = '模型文件不存在'

# 爬虫请求
try:
    html = await fetch(session, url)
except asyncio.TimeoutError:
    logger.warning(f'请求超时: {url}')
except aiohttp.ClientError as e:
    logger.warning(f'请求错误: {url} - {e}')
```

---

## 17. Coding Plan 使用指南

### 17.1 开发新功能时的上下文

当使用 Coding Plan 开发新功能时，提供以下上下文信息可以获得更准确的结果：

```
### 功能需求
[描述具体功能]

### 相关模块
- 主要修改: [模块名]
- 关联模块: [模块名]

### 关键文件
- [文件路径]: [作用说明]

### 参考代码
[类似功能的代码位置]

### 数据模型
[涉及的数据表和字段]
```

### 17.2 常见开发场景模板

#### 场景 1: 添加新的数据统计页面

```
需求: 添加统计页面，展示打标数据统计
涉及文件:
- bustag/app/index.py (添加路由)
- bustag/app/views/stats.tpl (新建模板)
- bustag/spider/db.py (添加统计查询函数)

参考代码:
- 推荐页面路由 (/)
- get_items() 函数

数据模型:
- Item 表
- ItemRate 表
```

#### 场景 2: 添加新的 API 接口

```
需求: 添加 REST API 返回 JSON 数据
涉及文件:
- bustag/app/index.py (添加路由)
- 可能需要: bustag/spider/db.py (查询函数)

参考代码:
- 现有路由的模式
- Bottle response.json 使用方式

返回格式:
{
  "success": true,
  "data": [...],
  "total": 100
}
```

#### 场景 3: 优化模型效果

```
需求: 尝试不同的分类模型，比较效果
涉及文件:
- bustag/model/classifier.py (修改 create_model, train)
- bustag/model/prepare.py (可能需要修改特征)

参考代码:
- 现有 train() 函数
- evaluate() 函数

评估指标:
- precision, recall, f1
```

### 17.3 代码修改检查清单

完成功能开发后，使用以下清单验证：

- [ ] 代码风格符合项目规范（ruff format）
- [ ] 类型注解完整（mypy 检查）
- [ ] 添加了必要的错误处理
- [ ] 更新了相关测试用例
- [ ] 文档字符串完整
- [ ] 导入语句按标准库/第三方/本地模块分组
- [ ] 没有硬编码的配置值（使用 APP_CONFIG）
- [ ] 数据库操作有事务保护

---

*文档版本: 0.3.0 | 最后更新: 2024*
