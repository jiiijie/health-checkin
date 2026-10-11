# 小眠 · AI 健康打卡小管家 🌿

一个温柔的智能健康助手：通过自然对话记录饮食、睡眠、运动、饮水，**自动估算卡路里并基于 TDEE 个性化评价**，智能对比目标给出主动提醒，每晚生成当日总结与改善建议。后端 FastAPI + DeepSeek，前端零构建原生三件套（支持深色模式），数据本地 JSON 持久化。

## ✨ 核心功能

- **对话式打卡**：直接说"今天喝了一大瓶水"，AI 解析并结构化为记录；无关闲聊则正常陪伴。
- **快捷打卡**：饮食/睡眠/运动/饮水四类模板化录入，**不依赖 AI 解析也能稳定保存**。
- **智能卡路里估算**：
  - 饮食记录自动调用 DeepSeek 估算热量，返回份量、食材、烹饪方式等营养细节
  - 基于个人档案（身高/体重/年龄/活动系数）计算 TDEE，按占比给出个性化评价（偏低/适中/偏高/超标）
  - 混合方案兜底：关键词匹配常见食物 + AI 兜底，兼顾速度与准确性
- **智能餐次分类**：AI 根据用餐时间 + 食物内容自动判断早餐/午餐/晚餐/加餐，容错处理跨时段场景
- **完整增删改查**：每条记录可查询、编辑、删除，全链路 RESTful。
- **今日目标进度**：正则解析饮水量(ml)、睡眠时长(小时)、运动时长(分钟)、卡路里摄入，对照个人档案目标绘制进度条。
- **主动提醒**：基于真实记录与目标，温柔提示饮水不足、运动不足、睡眠不足、熬夜、久坐、卡路里超标。
- **每日自动总结**：后台定时任务每晚自动生成并持久化当日总结 + 建议，统计页可回看历史总结。
- **个人档案**：身高/体重/目标等，对话中透露的信息自动同步进档案。
- **深色模式**：跟随系统主题或手动切换，保护视力。
- **周趋势统计**：可视化展示近 7 天卡路里、饮水量、睡眠时长变化趋势。

## 🧱 技术栈

| 层 | 选型 |
|----|------|
| 后端 | FastAPI + Uvicorn |
| AI | DeepSeek Chat API（`deepseek-chat`） |
| 数据校验 | Pydantic v2 |
| 前端 | 原生 HTML / CSS / JavaScript（无框架、无构建，支持深色模式） |
| 持久化 | 本地 JSON 文件（`data/`） |
| 依赖管理 | pyproject.toml + uv（也可用 pip） |

## 📁 项目结构

```
health-checkin/
├── main.py              # FastAPI 入口：路由、启动生命周期、后台定时任务
├── app/
│   ├── ai_service.py    # DeepSeek 对话封装、响应 JSON 解析、总结生成、卡路里估算
│   ├── analysis.py      # 健康数据正则解析、TDEE 计算、目标进度、主动提醒
│   ├── calories.py      # 卡路里估算混合方案（关键词匹配 + AI 兜底）
│   ├── data_store.py    # JSON 读写、记录/档案/历史/总结持久化
│   └── models.py        # Pydantic 数据模型
├── static/              # 前端：index.html / style.css / app.js（含深色模式）
├── data/                # 运行时数据（已 .gitignore，不入库）
│   ├── records.json         # 打卡记录
│   ├── profile.json         # 个人档案
│   ├── chat_history.json    # 对话历史（持久化）
│   └── summaries.json       # 每日总结（自动/手动生成）
├── .env                 # 环境变量配置（DeepSeek API Key）
├── .env.example         # 环境变量示例
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

> 💡 **提示**：首次启动时，系统会自动创建 `data/` 目录及初始 JSON 文件。

## 🔌 API 一览

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/` | 首页（单页应用） |
| POST | `/api/chat` | 对话打卡，返回回复/记录/提醒/卡路里估算 |
| POST | `/api/quick-record` | 快捷打卡，直接保存不依赖 AI |
| GET | `/api/records` | 全部记录，支持 `?date=YYYY-MM-DD` 过滤 |
| GET | `/api/records/{id}` | 查询单条记录 |
| PUT | `/api/records/{id}` | 编辑记录内容/类别 |
| DELETE | `/api/records/{id}` | 删除记录 |
| GET | `/api/goals` | 今日目标进度（饮水/睡眠/运动/卡路里）+ 提醒 |
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
- `datetime`：ISO 8601 完整时间戳，如 `2026-10-11T14:30:00`（新增标准字段，旧数据启动时自动回填）

## 🎯 卡路里评价算法

基于 **TDEE（每日总能量消耗）** 的个性化评价：

1. **计算 TDEE**：通过 Mifflin-St Jeor 公式计算 BMR，再乘以活动系数
2. **计算占比**：单日卡路里摄入 / TDEE × 100%
3. **评价等级**：
   - `< 60%`：偏低，建议增加营养
   - `60% - 90%`：适中，保持良好
   - `90% - 110%`：偏高，注意控制
   - `> 110%`：超标，建议调整饮食结构

> 📊 评价标准根据个人档案（身高/体重/年龄/活动水平）动态计算，非固定阈值。

## 📜 开发约定

改动请遵循 [CLAUDE.md](CLAUDE.md) 开发宪法五条原则：密钥安全、数据可靠持久化、温柔风格、基于真实数据主动提醒、每日总结。

## 📝 更新日志

### v1.0.0（当前版本）

- ✅ 对话式打卡 + 快捷打卡双模式
- ✅ 智能卡路里估算与 TDEE 个性化评价
- ✅ 智能餐次分类（AI 判断早/午/晚/加餐）
- ✅ 完整 CRUD 操作
- ✅ 今日目标进度可视化
- ✅ 主动健康提醒（饮水/运动/睡眠/久坐/熬夜/卡路里）
- ✅ 每日自动总结与建议
- ✅ 个人档案管理与自动同步
- ✅ 深色模式支持
- ✅ 周趋势统计图表
- ✅ 历史总结回看

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License

---

<div align="center">

**小眠** — 用温柔的对话，守护你的每一天 🌙

</div>
