import json
from datetime import datetime
from pathlib import Path

# 使用绝对路径，避免 uvicorn reload 时工作目录变化
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
RECORDS_FILE = DATA_DIR / "records.json"


def _ensure_data_dir():
    DATA_DIR.mkdir(exist_ok=True)


def _load_all_records() -> list[dict]:
    _ensure_data_dir()
    if not RECORDS_FILE.exists():
        return []
    with open(RECORDS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_all_records(records: list[dict]):
    _ensure_data_dir()
    with open(RECORDS_FILE, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)


def save_record(record: dict):
    records = _load_all_records()
    records.append(record)
    _save_all_records(records)


def get_records_by_date(date_str: str) -> list[dict]:
    records = _load_all_records()
    return [r for r in records if r.get("date") == date_str]


def get_all_records(limit: int = 100) -> list[dict]:
    records = _load_all_records()
    return records[-limit:]


def get_today_str() -> str:
    return datetime.now().strftime("%Y-%m-%d")
