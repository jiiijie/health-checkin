# 小眠 · AI 健康打卡小管家 🌿

一个温柔的健康打卡助手：用自然对话记录饮食、睡眠、运动、饮水，自动对比目标给出主动提醒，并在每晚生成当日总结。后端 FastAPI + DeepSeek，前端零构建原生三件套，数据本地 JSON 持久化。

## ✨ 核心功能

- **对话式打卡**：直接说"今天喝了一大瓶水"，AI 解析并结构化为记录；无关闲聊则正常陪伴。
- **快捷打卡**：饮食/睡眠/运动/饮水四类模板化录入，**不依赖 AI 解析也能稳定保存**。
- **完整增删改查**：每条记录可查询、编辑、删除，全链路 RESTful。
- **今日目标进度**：正则解析饮水量(ml)、睡眠时长(小时)、运动时长(分钟)，对照个人档案目标绘制进度条。
- **主动提醒**：基于真实记录与目标，温柔提示饮水不足、运动不足、睡眠不足、熬夜、久坐。
- **每日自动总结**：后台定时任务每晚自动生成并持久化当日总结 + 建议，统计页可回看历史总结。
- **个人档案**：身高/体重/目标等，对话中透露的信息自动同步进档案。

## 🧱 技术栈

| 层 | 选型 |
|----|------|
| 后端 | FastAPI + Uvicorn |
| AI | DeepSeek Chat API（`deepseek-chat`） |
| 数据校验 | Pydantic v2 |
| 前端 | 原生 HTML / CSS / JavaScript（无框架、无构建） |
| 持久化 | 本地 JSON 文件（`data/`） |
| 依赖管理 | pyproject.toml + uv（也可用 pip） |

## 📁 项目结构

```
health-checkin/
├── main.py              # FastAPI 入口：路由、启动生命周期、后台定时任务
├── app/
│   ├── ai_service.py    # DeepSeek 对话封装、响应 JSON 解析、总结生成
│   ├── analysis.py      # 健康数据正则解析、目标计算、主动提醒
│   ├── data_store.py    # JSON 读写、记录/档案/历史/总结持久化
│   └── models.py        # Pydantic 数据模型
├── static/              # 前端：index.html / style.css / app.js
├── data/                # 运行时数据（已 .gitignore，不入库）
│   ├── records.json         # 打卡记录
│   ├── profile.json         # 个人档案
│   ├── chat_history.json    # 对话历史（持久化）
│   └── summaries.json       # 每日总结（自动/手动生成）
├── CLAUDE.md            # 开发宪法（核心原则）
└── pyproject.toml       # 项目与依赖定义
```

## 🚀 快速开始

### 1. 配置环境变量

在项目根目录创建 `.env`（参考 `.env.example`）：

```env
DEEPSEEK_API_KEY=你的_DeepSeek_密钥
```

> ⚠️ 密钥只放在 `.env`，切勿提交到 Git。`.gitignore` 已忽略 `.env` 与 `data/*.json`。

### 2. 安装依赖

```powershell
# 使用 uv（推荐）
uv sync

# 或使用 pip
.venv\Scripts\pip3.exe install -e .
```

### 3. 启动服务

```powershell
.venv\Scripts\python.exe main.py
```

或：

```powershell
.venv\Scripts\uvicorn.exe main:app --reload
```

浏览器打开 <http://localhost:8000> 即可使用。

## 🔌 API 一览

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/` | 首页（单页应用） |
| POST | `/api/chat` | 对话打卡，返回回复/记录/提醒 |
| POST | `/api/quick-record` | 快捷打卡，直接保存不依赖 AI |
| GET | `/api/records` | 全部记录，支持 `?date=YYYY-MM-DD` 过滤 |
| GET | `/api/records/{id}` | 查询单条记录 |
| PUT | `/api/records/{id}` | 编辑记录内容/类别 |
| DELETE | `/api/records/{id}` | 删除记录 |
| GET | `/api/goals` | 今日目标进度（饮水/睡眠/运动）+ 提醒 |
| GET | `/api/summary/today` | 实时生成今日总结 |
| GET | `/api/summaries` | 历史每日总结列表 |
| GET | `/api/summaries/{date}` | 某天已保存的总结 |
| POST | `/api/summaries/generate` | 生成并持久化某天总结（`?date=` 可选） |
| GET | `/api/profile` | 读取个人档案 |
| POST | `/api/profile` | 保存个人档案 |

## 🕒 时间格式

每条记录同时保存三个字段，兼顾兼容与规范：

- `date`：`YYYY-MM-DD`（按日过滤）
- `timestamp`：`HH:MM:SS`（前端展示、久坐/熬夜判定）
- `datetime`：ISO 8601 完整时间戳，如 `2026-09-29T14:30:00`（新增标准字段，旧数据启动时自动回填）

## 📜 开发约定

改动请遵循 [CLAUDE.md](CLAUDE.md) 开发宪法五条原则：密钥安全、数据可靠持久化、温柔风格、基于真实数据主动提醒、每日总结。
