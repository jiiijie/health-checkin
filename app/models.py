from pydantic import BaseModel
from enum import Enum


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


class DaySummary(BaseModel):
    date: str
    summary: str
    suggestion: str
    records: list[HealthRecord] = []


class ChatResponse(BaseModel):
    reply: str
    records: list[HealthRecord] = []
    alerts: list[str] = []
