# CLAUDE.md — 小眠·AI健康打卡小管家 开发宪法

## 项目使命
小眠是一个温暖的 AI 健康打卡助手，帮助用户记录饮食、睡眠、运动等日常习惯，
并给出温柔的健康建议，尤其关注熬夜、久坐、饮水不足等问题。

## 技术栈
- **后端**: Python 3.14 + FastAPI + Uvicorn
- **前端**: 原生 HTML / CSS / JavaScript（无框架）
- **AI**: DeepSeek Chat API（通过 httpx 调用）
- **存储**: 本地 JSON 文件（data/records.json）
- **配置**: python-dotenv 读取 .env 文件

## 核心原则
1. **API Key 安全**: 绝不在代码中硬编码 API Key，必须从环境变量 `DEEPSEEK_API_KEY` 读取
2. **数据持久化**: 所有打卡记录保存在本地 JSON 文件中，重启不丢失
3. **温柔风格**: 小眠的语气始终温柔、关心、鼓励，不批评用户
4. **主动提醒**: 检测到熬夜（>23:00 未睡）、久坐（>2h）、饮水不足时主动提醒
5. **每日总结**: 每天自动生成一条总结 + 一条建议

## 项目结构
```
health-checkin/
├── CLAUDE.md              # 本文件 — 开发宪法
├── .env.example           # 环境变量示例
├── .gitignore
├── pyproject.toml
├── main.py                # 入口文件
├── app/
│   ├── __init__.py
│   ├── models.py          # 数据模型
│   ├── ai_service.py      # DeepSeek API 服务
│   └── data_store.py      # 本地 JSON 存储
└── static/
    ├── index.html          # 前端页面
    ├── style.css           # 样式
    └── app.js              # 前端逻辑
```

## API 接口
| 方法   | 路径              | 说明               |
|--------|-------------------|--------------------|
| GET    | /                 | 前端页面           |
| POST   | /api/chat         | 发送消息给小眠     |
| GET    | /api/records      | 获取历史记录       |
| GET    | /api/summary/today| 获取今日总结       |

## 开发规范
- 所有 API 返回 JSON 格式
- 错误信息用中文返回
- 时间格式统一使用 ISO 8601
- 文件编码统一 UTF-8
