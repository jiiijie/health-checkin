import uuid
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path
from dotenv import load_dotenv

from app.models import ChatRequest, ChatResponse, HealthRecord, DaySummary, UserProfile, ProfileResponse
from app.ai_service import chat_with_ai, generate_summary
from app.data_store import (
    save_record, get_records_by_date, get_all_records, get_today_str,
    load_profile, save_profile,
)

# 使用绝对路径加载 .env 文件，避免 uvicorn reload 时工作目录变化导致找不到
load_dotenv(Path(__file__).parent / ".env")

chat_histories: dict[str, list[dict]] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


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
    history.append({"role": "user", "content": req.message})

    result = await chat_with_ai(req.message, history)

    history.append({"role": "assistant", "content": result["reply"]})

    today = get_today_str()
    now_str = datetime.now().strftime("%H:%M:%S")
    saved_records = []

    for r in result.get("records", []):
        record = {
            "id": str(uuid.uuid4()),
            "category": r.get("category", "other"),
            "content": r.get("content", ""),
            "timestamp": now_str,
            "date": today,
        }
        save_record(record)
        saved_records.append(record)

    alerts = result.get("alerts", [])
    hour = datetime.now().hour
    if hour >= 23 or hour < 6:
        alerts.append("已经很晚啦，早点休息对身体好哦～")

    return ChatResponse(
        reply=result["reply"],
        records=[HealthRecord(**r) for r in saved_records],
        alerts=alerts,
    )


@app.get("/api/records")
async def get_records(date: str = None):
    if date:
        return get_records_by_date(date)
    return get_all_records()


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
