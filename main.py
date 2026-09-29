import uuid
import asyncio
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path
from dotenv import load_dotenv

from app.models import ChatRequest, ChatResponse, HealthRecord, DaySummary, UserProfile, ProfileResponse, QuickRecordRequest, UpdateRecordRequest, RecordResponse, GoalsResponse, GoalItem, SavedSummary, SummariesResponse, SummaryResponse
from app.ai_service import chat_with_ai, generate_summary
from app.analysis import compute_goals, build_alerts
from app.data_store import (
    save_record, get_records_by_date, get_all_records, get_today_str,
    load_profile, save_profile, update_record, delete_record, get_record_by_id,
    load_chat_histories, save_chat_histories, load_summaries, save_summary, get_summary,
)

# 使用绝对路径加载 .env 文件，避免 uvicorn reload 时工作目录变化导致找不到
load_dotenv(Path(__file__).parent / ".env")

chat_histories: dict[str, list[dict]] = {}

# 每日自动生成总结的时间（时、分）与对话历史上限
SUMMARY_HOUR, SUMMARY_MINUTE = 22, 30
MAX_HISTORY = 60


def _persist_history(session_id: str, history: list[dict]):
    """写回对话历史到磁盘，并限制长度防止无限增长"""
    if len(history) > MAX_HISTORY:
        del history[:-MAX_HISTORY]
    chat_histories[session_id] = history
    save_chat_histories(chat_histories)


def _is_meta_record(category: str, content: str) -> bool:
    """判断一条记录是否是“总结/查询请求”这类元操作（不应作为健康数据保存）"""
    if not content:
        return True
    meta_keywords = ["请求总结", "用户请求", "总结今天", "总结我的一天", "回顾今天", "要求总结", "想要总结"]
    if any(k in content for k in meta_keywords):
        return True
    # other 类别且内容为空或极短无意义
    if category == "other" and len(content.strip()) < 2:
        return True
    return False


def _detect_health_message(msg: str) -> dict | None:
    """关键词检测：当 AI 没返回 JSON 时，根据用户消息内容自动识别类别"""
    msg_lower = msg.lower()
    # 饮水
    if any(k in msg_lower for k in ["喝水", "喝了", "ml", "毫升", "一杯水", "一瓶水"]):
        return {"category": "water"}
    # 睡眠
    if any(k in msg_lower for k in ["睡觉", "睡了", "睡的", "入睡", "起床", "昨晚", "睡眠"]):
        return {"category": "sleep"}
    # 运动
    if any(k in msg_lower for k in ["跑步", "运动", "健身", "游泳", "瑜伽", "散步", "骑车", "分钟"]):
        return {"category": "exercise"}
    # 饮食
    if any(k in msg_lower for k in ["吃了", "早餐", "午餐", "晚餐", "早饭", "午饭", "晚饭", "喝了一杯", "外卖"]):
        return {"category": "diet"}
    return None


async def _generate_and_save_summary(date_str: str) -> dict | None:
    """为指定日期生成并持久化总结，无记录时返回 None"""
    records = get_records_by_date(date_str)
    if not records:
        return None
    result = await generate_summary(records)
    entry = {
        "summary": result.get("summary", ""),
        "suggestion": result.get("suggestion", ""),
        "generated_at": datetime.now().strftime("%H:%M:%S"),
        "auto": True,
    }
    save_summary(date_str, entry)
    return entry


async def _daily_summary_loop():
    """后台定时任务：每天到达指定时间后自动生成并保存当日总结（开发宪法第 5 条）"""
    while True:
        try:
            now = datetime.now()
            today = now.strftime("%Y-%m-%d")
            if (now.hour, now.minute) >= (SUMMARY_HOUR, SUMMARY_MINUTE) and not get_summary(today):
                await _generate_and_save_summary(today)
        except Exception:
            pass
        await asyncio.sleep(60)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时从磁盘加载对话历史
    chat_histories.update(load_chat_histories())
    # 启动每日总结后台任务
    task = asyncio.create_task(_daily_summary_loop())
    yield
    task.cancel()


app = FastAPI(title="小眠·AI健康打卡小管家", lifespan=lifespan)
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def index():
    return FileResponse("static/index.html")


@app.post("/api/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    session_id = "default"
    if session_id not in chat_histories:
        chat_histories[session_id] = []

    history = chat_histories[session_id]

    # 加载用户档案和今日记录，传入 AI 上下文
    profile = load_profile()
    today_records = get_records_by_date(get_today_str())
    result = await chat_with_ai(req.message, history, profile=profile, records=today_records)

    # AI 调用完成后，再将本轮对话加入历史（避免 user_message 在 messages 中出现两次）
    history.append({"role": "user", "content": req.message})
    history.append({"role": "assistant", "content": result["reply"]})
    _persist_history(session_id, history)

    today = get_today_str()
    now_str = datetime.now().strftime("%H:%M:%S")
    saved_records = []

    for r in result.get("records", []):
        category = r.get("category", "other")
        content = r.get("content", "")
        # 过滤掉“总结/查询请求”这类误记录的垃圾数据
        if _is_meta_record(category, content):
            continue
        record = {
            "id": str(uuid.uuid4()),
            "category": category,
            "content": content,
            "timestamp": now_str,
            "date": today,
        }
        save_record(record)
        saved_records.append(record)

    # 兆底：AI 没返回 JSON 但用户消息明显包含健康信息，直接保存
    if not saved_records:
        fallback = _detect_health_message(req.message)
        if fallback:
            record = {
                "id": str(uuid.uuid4()),
                "category": fallback["category"],
                "content": req.message,
                "timestamp": now_str,
                "date": today,
            }
            save_record(record)
            saved_records.append(record)

    alerts = result.get("alerts", [])
    # 基于今日记录 + 档案目标生成真实提醒（饮水/运动/睡眠/熬夜/久坐）
    goal_alerts = build_alerts(compute_goals(get_records_by_date(get_today_str()), profile), get_records_by_date(get_today_str()), datetime.now())
    for a in goal_alerts:
        if a not in alerts:
            alerts.append(a)

    # 处理档案更新（对话中识别到的个人信息自动同步到档案）
    profile_update = result.get("profile_update", {})
    if profile_update:
        merged = {**profile, **profile_update}
        save_profile(merged)
        alerts.append(f"📝 已自动更新档案：{', '.join(profile_update.keys())}")

    return ChatResponse(
        reply=result["reply"],
        records=[HealthRecord(**r) for r in saved_records],
        alerts=alerts,
    )


# ===== 快捷打卡 API（直接保存，不依赖 AI 解析） =====
@app.post("/api/quick-record", response_model=ChatResponse)
async def quick_record(req: QuickRecordRequest):
    # 1. 先直接保存记录（保证一定成功）
    today = get_today_str()
    now_str = datetime.now().strftime("%H:%M:%S")
    record = {
        "id": str(uuid.uuid4()),
        "category": req.category.value,
        "content": req.content,
        "timestamp": now_str,
        "date": today,
    }
    save_record(record)

    # 2. 让 AI 生成友好回复（失败也不影响记录保存）
    message = req.message or req.content
    try:
        session_id = "default"
        if session_id not in chat_histories:
            chat_histories[session_id] = []
        history = chat_histories[session_id]
        profile = load_profile()
        today_records = get_records_by_date(get_today_str())
        result = await chat_with_ai(message, history, profile=profile, records=today_records)
        reply = result["reply"]
        # 更新对话历史
        history.append({"role": "user", "content": message})
        history.append({"role": "assistant", "content": reply})
        _persist_history(session_id, history)
    except Exception:
        # AI 失败时用默认回复
        category_names = {"water": "喝水", "diet": "饮食", "exercise": "运动", "sleep": "睡眠", "other": "记录"}
        name = category_names.get(req.category.value, "记录")
        reply = f"已记下你的{name}啦～继续加油！💪"

    alerts = build_alerts(compute_goals(get_records_by_date(get_today_str()), load_profile()), get_records_by_date(get_today_str()), datetime.now())

    return ChatResponse(
        reply=reply,
        records=[HealthRecord(**record)],
        alerts=alerts,
    )


@app.get("/api/records")
async def get_records(date: str = None):
    if date:
        return get_records_by_date(date)
    return get_all_records()


@app.get("/api/records/{record_id}", response_model=RecordResponse)
async def get_one_record(record_id: str):
    record = get_record_by_id(record_id)
    if not record:
        return RecordResponse(success=False, message="记录不存在")
    return RecordResponse(success=True, record=HealthRecord(**record))


@app.put("/api/records/{record_id}", response_model=RecordResponse)
async def modify_record(record_id: str, req: UpdateRecordRequest):
    updates = req.model_dump(exclude_none=True)
    # HealthCategory 枚举转字符串
    if "category" in updates and hasattr(updates["category"], "value"):
        updates["category"] = updates["category"].value
    if not updates:
        return RecordResponse(success=False, message="没有需要更新的字段")
    updated = update_record(record_id, updates)
    if not updated:
        return RecordResponse(success=False, message="记录不存在")
    return RecordResponse(success=True, record=HealthRecord(**updated), message="修改成功")


@app.delete("/api/records/{record_id}", response_model=RecordResponse)
async def remove_record(record_id: str):
    ok = delete_record(record_id)
    if not ok:
        return RecordResponse(success=False, message="记录不存在")
    return RecordResponse(success=True, message="删除成功")


@app.get("/api/summary/today", response_model=DaySummary)
async def today_summary():
    today = get_today_str()
    records = get_records_by_date(today)

    if not records:
        return DaySummary(
            date=today,
            summary="今天还没有打卡记录哦，快来和小眠聊聊吧～",
            suggestion="记得记录今天的饮食和作息呀！",
            records=[],
        )

    result = await generate_summary(records)
    return DaySummary(
        date=today,
        summary=result.get("summary", ""),
        suggestion=result.get("suggestion", ""),
        records=[HealthRecord(**r) for r in records],
    )


@app.get("/api/goals", response_model=GoalsResponse)
async def goals():
    today_records = get_records_by_date(get_today_str())
    profile = load_profile()
    goals_data = compute_goals(today_records, profile)
    alerts = build_alerts(goals_data, today_records, datetime.now())
    return GoalsResponse(
        water=GoalItem(**goals_data["water"]),
        sleep=GoalItem(**goals_data["sleep"]),
        exercise=GoalItem(**goals_data["exercise"]),
        alerts=alerts,
    )


# ===== 历史每日总结 API =====
@app.get("/api/summaries", response_model=SummariesResponse)
async def list_summaries():
    summaries = load_summaries()
    items = [
        SavedSummary(date=d, **{k: v.get(k, "") for k in ("summary", "suggestion", "generated_at", "auto")})
        for d, v in sorted(summaries.items(), reverse=True)
    ]
    return SummariesResponse(success=True, summaries=items)


@app.get("/api/summaries/{date}", response_model=SummaryResponse)
async def get_saved_summary(date: str):
    entry = get_summary(date)
    if not entry:
        return SummaryResponse(success=False, message="该日期没有保存的总结")
    return SummaryResponse(success=True, data=SavedSummary(date=date, **{k: entry.get(k, "") for k in ("summary", "suggestion", "generated_at", "auto")}))


@app.post("/api/summaries/generate", response_model=SummaryResponse)
async def generate_daily_summary(date: str = None):
    target = date or get_today_str()
    entry = await _generate_and_save_summary(target)
    if not entry:
        return SummaryResponse(success=False, message="该日期没有打卡记录，无法生成总结")
    return SummaryResponse(success=True, data=SavedSummary(date=target, **entry))


# ===== 个人档案 API =====
@app.get("/api/profile")
async def get_profile():
    return load_profile()


@app.post("/api/profile", response_model=ProfileResponse)
async def update_profile(profile: UserProfile):
    data = profile.model_dump(exclude_none=True)
    save_profile(data)
    return ProfileResponse(success=True, profile=data)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
