from pydantic import BaseModel
from enum import Enum
from typing import Optional


class HealthCategory(str, Enum):
    DIET = "diet"
    SLEEP = "sleep"
    EXERCISE = "exercise"
    WATER = "water"
    OTHER = "other"


class ChatRequest(BaseModel):
    message: str


class HealthRecord(BaseModel):
    id: str = ""
    category: HealthCategory
    content: str
    timestamp: str = ""
    date: str = ""
    datetime: str = ""  # ISO 8601 完整时间戳，如 2026-09-29T14:30:00（新增兼容字段）


class DaySummary(BaseModel):
    date: str
    summary: str
    suggestion: str
    records: list[HealthRecord] = []


class ChatResponse(BaseModel):
    reply: str
    records: list[HealthRecord] = []
    alerts: list[str] = []


class UserProfile(BaseModel):
    nickname: Optional[str] = None
    gender: Optional[str] = None
    age: Optional[float] = None
    height: Optional[float] = None
    weight: Optional[float] = None
    waist: Optional[float] = None
    arm: Optional[float] = None
    leg: Optional[float] = None
    chest: Optional[float] = None
    target_weight: Optional[float] = None
    daily_water: Optional[float] = 2000
    daily_exercise: Optional[float] = 30
    target_sleep: Optional[float] = 8


class ProfileResponse(BaseModel):
    success: bool = True
    profile: Optional[dict] = None


class QuickRecordRequest(BaseModel):
    category: HealthCategory
    content: str
    message: str = ""


class UpdateRecordRequest(BaseModel):
    category: Optional[HealthCategory] = None
    content: Optional[str] = None


class RecordResponse(BaseModel):
    success: bool = True
    record: Optional[HealthRecord] = None
    message: str = ""


class GoalItem(BaseModel):
    total: float = 0
    target: float = 0
    percent: int = 0
    unit: str = ""


class GoalsResponse(BaseModel):
    water: GoalItem = GoalItem()
    sleep: GoalItem = GoalItem()
    exercise: GoalItem = GoalItem()
    alerts: list[str] = []


class SavedSummary(BaseModel):
    date: str
    summary: str = ""
    suggestion: str = ""
    generated_at: str = ""
    auto: bool = False


class SummariesResponse(BaseModel):
    success: bool = True
    summaries: list[SavedSummary] = []


class SummaryResponse(BaseModel):
    success: bool = True
    data: Optional[SavedSummary] = None
    message: str = ""
