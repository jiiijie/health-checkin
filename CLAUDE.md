# CLAUDE.md — 小眠·AI健康打卡小管家 开发宪法

## 项目简介
小眠是一个温暖的 AI 健康打卡助手，帮助用户通过自然对话记录饮食、睡眠、运动、饮水等日常习惯，并给出温柔的健康建议。重点关注**熬夜、久坐、饮食不规律**等风险，每晚自动生成当日总结，并支持回看一周趋势。

## 技术栈
- **后端**: Python 3.14 + FastAPI + Uvicorn + Pydantic v2
- **前端**: 原生 HTML / CSS / JavaScript（无框架、无构建）
- **AI**: DeepSeek Chat API（`deepseek-chat` 模型，通过 httpx 调用）
- **异步**: asyncio（后台定时任务、并发 API 调用）
- **存储**: 本地 JSON 文件（`data/` 目录）
- **配置**: python-dotenv 读取 `.env` 文件

## 核心原则
1. **API Key 安全**: 绝不在代码中硬编码 API Key，必须从环境变量 `DEEPSEEK_API_KEY` 读取
2. **数据持久化**: 所有打卡记录、对话历史、每日总结保存在本地 JSON 文件中，重启不丢失
3. **温柔风格**: 小眠的语气始终温柔、关心、鼓励，不批评用户
4. **主动提醒**: 基于真实数据与档案目标，检测熬夜（>23:00 未睡）、久坐（>2h）、饮水不足、运动不足、睡眠不足、饮食不规律（漏餐/深夜进食）时主动提醒
5. **每日总结**: 每天 22:30 自动生成一条总结 + 一条建议并持久化，统计页可回看历史总结

## 项目结构
```
health-checkin/
├── CLAUDE.md              # 本文件 — 开发宪法
├── README.md              # 项目说明文档
├── .env.example           # 环境变量示例
├── .gitignore             # 忽略 .env 与 data/*.json
├── pyproject.toml         # 项目与依赖定义
├── main.py                # FastAPI 入口：路由、启动生命周期、后台定时任务
├── app/
│   ├── __init__.py
│   ├── models.py          # Pydantic 数据模型
│   ├── ai_service.py      # DeepSeek API 封装、响应解析、总结生成
│   ├── analysis.py        # 健康数据正则解析、目标计算、主动提醒、周趋势聚合
│   └── data_store.py      # JSON 读写、记录/档案/对话历史/总结持久化
├── static/                # 前端：index.html / style.css / app.js
└── data/                  # 运行时数据（已 .gitignore，不入库）
    ├── records.json       # 打卡记录
    ├── profile.json       # 个人档案
    ├── chat_history.json  # 对话历史（持久化）
    └── summaries.json     # 每日总结（自动/手动生成）
```

## API 接口
| 方法   | 路径                       | 说明                               |
|--------|----------------------------|------------------------------------|
| GET    | /                          | 前端页面（单页应用）               |
| POST   | /api/chat                  | 对话打卡，返回回复/记录/提醒       |
| POST   | /api/quick-record          | 快捷打卡，直接保存不依赖 AI        |
| GET    | /api/records               | 全部记录，支持 `?date=` 过滤       |
| GET    | /api/records/{id}          | 查询单条记录                       |
| PUT    | /api/records/{id}          | 编辑记录内容/类别                  |
| DELETE | /api/records/{id}          | 删除记录                           |
| GET    | /api/goals                 | 今日目标进度（饮水/睡眠/运动）+ 提醒 |
| GET    | /api/weekly                | 一周趋势聚合（日均/达标天数/点评） |
| GET    | /api/summary/today         | 实时生成今日总结                   |
| GET    | /api/summaries             | 历史每日总结列表                   |
| GET    | /api/summaries/{date}      | 某天已保存的总结                   |
| POST   | /api/summaries/generate    | 生成并持久化某天总结               |
| GET    | /api/profile               | 读取个人档案                       |
| POST   | /api/profile               | 保存个人档案                       |

## 开发规范
- 所有 API 返回 JSON 格式
- 错误信息用中文返回
- 时间格式：每条记录同时保存 `date`(YYYY-MM-DD)、`timestamp`(HH:MM:SS)、`datetime`(ISO 8601) 三个字段，旧数据启动时自动回填 datetime
- 文件编码统一 UTF-8
- 提醒与统计逻辑优先用纯正则 + 规则实现，不依赖 AI，保证稳定可重复
- 前端资源引用加版本号（`?v=N`）以绕过浏览器缓存

## 禁止事项
以下行为在项目中**严格禁止**，违反即视为严重违规：

1. **禁止硬编码 API Key**：绝不允许在代码、配置文件、注释、文档中出现真实的 API Key、Token、密码。必须通过环境变量 `DEEPSEEK_API_KEY` 读取。
2. **禁止提交个人数据**：`.env`、`data/*.json`（含 records.json、profile.json、chat_history.json、summaries.json）已被 `.gitignore` 忽略，**绝不允许**手动 `git add -f` 强制提交。
3. **禁止删除或覆盖用户数据**：不得在代码中实现清空 records/profile/chat_history/summaries 的功能，除非用户显式触发（如删除单条记录）。
4. **禁止 AI 将元操作误存为记录**：当用户请求"总结/回顾/查询"时，AI 不得输出 `records` JSON，后端必须用 `_is_meta_record` 过滤。
5. **禁止破坏温柔风格**：AI 回复不得批评、说教、恐吓用户，不得使用"你必须""你应该""再这样下去会..."等负面表达。
6. **禁止无依据提醒**：主动提醒必须基于真实记录与档案目标计算，不得凭空生成。
7. **禁止修改历史提交**：已推送到 GitHub 的提交**绝不允许** `git push --force` 或 `git rebase` 覆盖，除非涉及密钥泄露等安全事件。
8. **禁止跳过测试直接发布**：任何涉及核心逻辑（打卡、提醒、总结、目标计算、周趋势）的改动，必须先通过端到端测试验证。
