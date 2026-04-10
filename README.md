# 基于机器学习的老司机车牌自动推荐系统
<img src="./bustag/app/static/images/logo.png" width="300">

**Bustag** 是一个自动车牌推荐系统, 系统原理为定时爬取最新车牌信息, 然后可以对车牌进行打标(标示是否喜欢), 打标车牌到一定数量可以进行训练并生成模型, 以后就可以基于此模型自动对下载的车牌进行预测是否喜欢, 可以过滤掉大量不喜欢的车牌, 节约时间

## 🆕 v0.3.0 更新 (2024)

本项目已完成全面现代化升级：

- ✅ **Python 3.10-3.13 支持** - 使用最新 Python 版本
- ✅ **依赖升级** - 所有关键依赖已更新到最新版本
- ✅ **移除 aspider** - 使用自定义 aiohttp 爬虫替代不再维护的 aspider
- ✅ **现代化构建** - 使用 pyproject.toml 和 setuptools
- ✅ **类型提示** - 代码增加类型注解
- ✅ **测试框架** - pytest + pytest-asyncio

### Python in Action 学习视频发布
[https://github.com/gxtrobot/pyinaction](https://github.com/gxtrobot/pyinaction)

为提高解决问题效率, 建了个qq群

**QQ群: 941894005**

注意, 该群仅讨论**python学习, 爬虫开发, Bustag系统bug, 运行问题**等, 请勿讨论无关主题

**免责声明:
本软件仅用于技术学习使用，禁止用于商业用途，使用本软件所造成的的后果由使用者承担！
如果你觉得这个软件不错, 可以请我喝杯冰阔落 ^_^.**

<p align="center">
<img src="./bustag/app/static/images/alipay.jpg" width="200">
<img src="./bustag/app/static/images/wechat_pay.jpg" width="200">
</p>

# 使用须知
只需在data目录下创建[config.ini](https://raw.githubusercontent.com/gxtrobot/bustag/master/data/config.ini), 然后启动系统, 访问localhost:8000

## 系统功能

- 自动抓取最新车牌信息, 抓取频率可以自定义
- 系统启动后自动开启一次下载, 然后安装设置抓取频率下载
- 车牌打标功能
- 模型训练, 基于当前所有打标数据训练模型
- 有了模型后, 自动预测判断是否喜欢
- 手动上传番号, 本地文件管理
- 数据库打标数据导入
- Docker 镜像一键运行, 省去新手配置项目的麻烦
- 项目访问地址: localhost:8000

## 系统截图(隐藏了左边封面图片)

- 推荐页面
  ![](./docs/recommend.png)

- 打标页面
  ![](./docs/tagit.png)

- 本地文件页面
  ![](./docs/local.png)

- 本地番号, 链接上传页面
  ![](./docs/local_upload.png)

- 模型页面
  ![](./docs/model.png)

- 数据页面
  ![](./docs/data.png)

## 快速开始

### 方式一：Docker 运行（推荐）

```bash
# 1. 创建数据目录
mkdir -p bustag/data && cd bustag

# 2. 创建配置文件 config.ini（必需）
cat > data/config.ini << 'EOF'
[download]
source = bus
root_path = https://www.busjav.com
count = 100
interval = 1800

[missav]
language = en
list_path = /en
proxy = http://127.0.0.1:7897
browser = chrome136
user_agent = Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36
cookie =

[auth]
admin_username = admin
admin_password = change-this-password
secret_key = change-this-secret-key
EOF

# 3. 启动容器
docker run --rm -d \
  --name bustag \
  -e TZ=Asia/Shanghai \
  -e PYTHONUNBUFFERED=1 \
  -v $(pwd)/data:/app/data \
  -p 8000:8000 \
  gxtrobot/bustag-app

# 4. 访问 http://localhost:8000
```

**Windows PowerShell:**
```powershell
# 创建配置文件后运行
docker run --rm -d --name bustag -e TZ=Asia/Shanghai -e PYTHONUNBUFFERED=1 -v ${PWD}/data:/app/data -p 8000:8000 gxtrobot/bustag-app
```

### 方式二：本地源码运行

**环境要求：** Python 3.10+ (支持 3.10, 3.11, 3.12, 3.13)

```bash
# 1. 克隆项目
git clone https://github.com/gxtrobot/bustag.git
cd bustag

# 2. 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate   # Windows

# 3. 安装依赖
pip install -e .

# 4. 创建配置文件
mkdir -p data
cat > data/config.ini << 'EOF'
[download]
source = bus
root_path = https://www.busjav.com
count = 100
interval = 1800

[missav]
language = en
list_path = /en
proxy = http://127.0.0.1:7897
browser = chrome136
user_agent = Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36
cookie =

[auth]
admin_username = admin
admin_password = change-this-password
secret_key = change-this-secret-key
EOF

# 5. 运行项目
python bustag/app/index.py

# 或使用 gunicorn（生产环境推荐）
pip install gunicorn
gunicorn bustag.app.index:app --bind='0.0.0.0:8000'
```

### 方式三：构建自定义 Docker 镜像

```bash
docker build -t bustag-app .
docker run --rm -d -e TZ=Asia/Shanghai -v $(pwd)/data:/app/data -p 8000:8000 bustag-app
```

## 如何使用项目

### 请按照以下顺序

1. 到打标页面进行打标, 达到一定数量(喜欢+不喜欢), 比如 300
2. 到其他页面训练模型
3. 坐等系统自动推荐
4. 在推荐页面进行确认(确认过的数据转为打标数据)
5. 积累更多打标数据, 再次训练模型, 打标数据越多模型效果越好

### data 目录文件说明

```
|____bus.db
|____config.ini
|____model
| |____ label_binarizer.pkl
| |____model.pkl
```

- **config.ini** - 系统配置文件(必须)
  - `[download]`
  - `source`: 站点适配器名称, 当前支持 `bus`、`missav`
  - `root_path`: bus网站主页地址, 爬虫起始地址
  - `count`: 每次下载总数, 建议500以下
  - `interval`: 每次下载间隔时间, 单位秒, 建议不低于1800秒
  - `[missav]`
  - `language`: 当前 MissAV adapter 使用的语言路径, 默认 `en`
  - `list_path`: MissAV 列表页路径, 默认 `/en`
  - `proxy`: MissAV 抓取代理
  - `browser`: `curl_cffi` 浏览器指纹, 默认 `chrome136`
  - `user_agent`: MissAV 请求使用的 User-Agent
  - `cookie`: 可留空, 建议用 `BUSTAG_MISSAV_COOKIE` 环境变量注入
  - `probe_url`: MissAV 探针URL, 可选（也可用环境变量 `BUSTAG_MISSAV_PROBE_URL`）
  - `[auth]`
  - `admin_username`: 默认管理员用户名
  - `admin_password`: 默认管理员密码, 建议通过 `BUSTAG_ADMIN_PASSWORD` 环境变量覆盖
  - `secret_key`: 登录 cookie 签名密钥, 建议通过 `BUSTAG_SECRET_KEY` 环境变量覆盖

### MissAV Cookie

推荐不要把 `missav.cookie` 直接写进 `data/config.ini`，而是在启动前注入环境变量：

```bash
export BUSTAG_MISSAV_COOKIE='user_uuid=...; cf_clearance=...'
export BUSTAG_MISSAV_PROXY='http://127.0.0.1:7897'
export BUSTAG_MISSAV_USER_AGENT='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36'
```

如果 `config.ini` 配置了代理但线上不需要，可在环境变量里显式清空：

```bash
export BUSTAG_MISSAV_PROXY=''
```

如果你在 WSL 的 conda 环境里运行，也可以这样：

```bash
conda run -n bustag env \
  BUSTAG_MISSAV_COOKIE='user_uuid=...; cf_clearance=...' \
  BUSTAG_MISSAV_PROXY='http://127.0.0.1:7897' \
  BUSTAG_MISSAV_USER_AGENT='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36' \
  python bustag/app/index.py
```

### MissAV Probe

建议在发布前执行探针确认站点可达和基础抓取能力：

```bash
make missav-probe
```

### One Command Start

项目根目录里提供了：

- `.env.example` - 本地环境变量模板
- `scripts/start.sh` - 读取 `.env` 后在 conda `bustag` 环境里启动项目

推荐这样使用：

```bash
cp .env.example .env
# 编辑 .env，填入你自己的 cookie
bash scripts/start.sh
```

或者：

```bash
make start-env
```

- **bus.db** - 数据库文件(可选)
- **model 目录** - 系统训练生成的模型

## 技术栈

| 组件 | 版本 | 用途 |
|------|------|------|
| Python | 3.10+ | 运行环境 |
| Bottle | 0.13+ | Web框架 |
| aiohttp | 3.9+ | 异步HTTP客户端 |
| Peewee | 3.17+ | ORM |
| scikit-learn | 1.5+ | 机器学习 |
| pandas | 2.2+ | 数据处理 |
| APScheduler | 3.10+ | 定时任务 |

## 开发

```bash
# 安装开发依赖
pip install -e ".[dev]"

# 运行测试
pytest

# 代码格式化
ruff format .

# 类型检查
mypy bustag
```

## 其他问题

1. **改变自动下载的频率**  
   修改config.ini的interval参数, 单位是秒

2. **是否可以使用代理**  
   目前系统还没加入代理功能, 可以在docker设置代理访问

3. **模型效果如何**  
   使用KNN模型, 准确率还可以, 召回率相对低一些. 打标数据越多效果越好

4. **要多少打标数据才能训练模型**  
   建议至少300条打标数据(包括喜欢和不喜欢)

5. **如何备份数据库**  
   数据库保存在 data/bus.db, 可以直接复制备份

## License

MIT License
