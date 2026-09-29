import json
from datetime import datetime
from pathlib import Path

# 使用绝对路径，避免 uvicorn reload 时工作目录变化
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
RECORDS_FILE = DATA_DIR / "records.json"
PROFILE_FILE = DATA_DIR / "profile.json"
CHAT_FILE = DATA_DIR / "chat_history.json"
SUMMARIES_FILE = DATA_DIR / "summaries.json"


def _ensure_data_dir():
    DATA_DIR.mkdir(exist_ok=True)


def _load_json_file(path: Path, default):
    """通用 JSON 读取，文件缺失/为空/损坏都返回 default"""
    _ensure_data_dir()
    if not path.exists():
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read().strip()
            return json.loads(content) if content else default
    except (json.JSONDecodeError, ValueError):
        return default


def _save_json_file(path: Path, data):
    _ensure_data_dir()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ===== 打卡记录 =====
def _load_all_records() -> list[dict]:
    _ensure_data_dir()
    if not RECORDS_FILE.exists():
        return []
    try:
        with open(RECORDS_FILE, "r", encoding="utf-8") as f:
            content = f.read().strip()
            return json.loads(content) if content else []
    except (json.JSONDecodeError, ValueError):
        return []


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


def get_record_by_id(record_id: str) -> dict | None:
    records = _load_all_records()
    for r in records:
        if r.get("id") == record_id:
            return r
    return None


def update_record(record_id: str, updates: dict) -> dict | None:
    """根据 id 更新记录，返回更新后的记录；找不到返回 None"""
    records = _load_all_records()
    for i, r in enumerate(records):
        if r.get("id") == record_id:
            # 只允许更新白名单字段，id/date 不变
            for key in ("category", "content", "timestamp"):
                if key in updates and updates[key] is not None:
                    records[i][key] = updates[key]
            _save_all_records(records)
            return records[i]
    return None


def delete_record(record_id: str) -> bool:
    """根据 id 删除记录，成功返回 True，找不到返回 False"""
    records = _load_all_records()
    new_records = [r for r in records if r.get("id") != record_id]
    if len(new_records) == len(records):
        return False
    _save_all_records(new_records)
    return True


def get_today_str() -> str:
    return datetime.now().strftime("%Y-%m-%d")


# ===== 个人档案 =====
def load_profile() -> dict:
    _ensure_data_dir()
    if not PROFILE_FILE.exists():
        return {}
    try:
        with open(PROFILE_FILE, "r", encoding="utf-8") as f:
            content = f.read().strip()
            return json.loads(content) if content else {}
    except (json.JSONDecodeError, ValueError):
        return {}


def save_profile(profile: dict):
    _ensure_data_dir()
    with open(PROFILE_FILE, "w", encoding="utf-8") as f:
        json.dump(profile, f, ensure_ascii=False, indent=2)


# ===== 对话历史持久化 =====
def load_chat_histories() -> dict:
    """加载所有会话的对话历史：{session_id: [{role, content}, ...]}"""
    return _load_json_file(CHAT_FILE, {})


def save_chat_histories(histories: dict):
    _save_json_file(CHAT_FILE, histories)


# ===== 每日总结持久化 =====
def load_summaries() -> dict:
    """加载历史每日总结：{date: {summary, suggestion, generated_at, auto}}"""
    return _load_json_file(SUMMARIES_FILE, {})


def save_summary(date_str: str, data: dict):
    summaries = load_summaries()
    summaries[date_str] = data
    _save_json_file(SUMMARIES_FILE, summaries)


def get_summary(date_str: str) -> dict | None:
    return load_summaries().get(date_str)
