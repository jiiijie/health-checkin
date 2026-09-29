"""健康记录分析：从文本记录中解析数值，计算目标进度并生成温柔提醒。

不依赖 AI，纯正则 + 规则，保证统计与提醒稳定可靠。
"""
import re
from datetime import datetime

# 常见饮水容器默认毫升数（当文本没有明确 ml 时兜底估算）
_WATER_UNIT_ML = [
    ("一大瓶", 1000),
    ("大瓶", 1000),
    ("一瓶", 500),
    ("一杯", 200),
    ("半杯", 100),
    ("一箱", 500),
]


def parse_water_ml(content: str) -> float:
    """从饮水记录文本中解析毫升数。优先匹配数字+ml/毫升，否则按容器估算。"""
    if not content:
        return 0.0
    # 明确写了 500ml / 500 毫升 / 1000ml
    m = re.search(r"(\d+(?:\.\d+)?)\s*(?:ml|毫升|ML|毫升水)", content)
    if m:
        return float(m.group(1))
    # 按容器关键词估算
    for kw, ml in _WATER_UNIT_ML:
        if kw in content:
            return float(ml)
    if "杯" in content:
        return 200.0
    if "瓶" in content:
        return 500.0
    return 0.0


def parse_sleep_hours(content: str) -> float:
    """从睡眠记录解析睡眠时长（小时），支持 '22:00~6:30'、'11点到7点' 等，跨零点。"""
    if not content:
        return 0.0
    # 形如 22:00~6:30 / 22:00-6:30 / 22:00 到 6:30
    m = re.search(r"(\d{1,2})[:：点](\d{2})?\s*[~\-到至到和跟]\s*(\d{1,2})[:：点](\d{2})?", content)
    if m:
        sh = int(m.group(1))
        sm = int(m.group(2) or 0)
        eh = int(m.group(3))
        em = int(m.group(4) or 0)
        start = sh * 60 + sm
        end = eh * 60 + em
        if end <= start:  # 跨零点
            end += 24 * 60
        hours = (end - start) / 60.0
        if 0 < hours <= 24:
            return round(hours, 1)
    # 直接写了 8小时 / 睡够7个半小时
    m2 = re.search(r"(\d+(?:\.\d+)?)\s*(?:小时|h|个小时)", content)
    if m2:
        h = float(m2.group(1))
        if 0 < h <= 24:
            return round(h, 1)
    return 0.0


def parse_exercise_minutes(content: str) -> float:
    """从运动记录解析运动分钟数，支持 '30分钟'、'1小时'、'跑步45min'。"""
    if not content:
        return 0.0
    m = re.search(r"(\d+(?:\.\d+)?)\s*(?:分钟|min|MIN)", content)
    if m:
        return float(m.group(1))
    m2 = re.search(r"(\d+(?:\.\d+)?)\s*(?:小时|h)", content)
    if m2:
        return float(m2.group(1)) * 60
    return 0.0


def _to_seconds(ts: str) -> int | None:
    """'HH:MM:SS' 或 'HH:MM' → 当天秒数。"""
    if not ts:
        return None
    parts = ts.split(":")
    try:
        h = int(parts[0])
        mnt = int(parts[1]) if len(parts) > 1 else 0
        s = int(parts[2]) if len(parts) > 2 else 0
        return h * 3600 + mnt * 60 + s
    except (ValueError, IndexError):
        return None


def compute_goals(records: list[dict], profile: dict) -> dict:
    """汇总今日各类达成量，与档案目标对比，返回结构化进度。"""
    water_target = float(profile.get("daily_water") or 2000)
    sleep_target = float(profile.get("target_sleep") or 8)
    exercise_target = float(profile.get("daily_exercise") or 30)

    water_total = sum(parse_water_ml(r.get("content", "")) for r in records if r.get("category") == "water")
    sleep_total = sum(parse_sleep_hours(r.get("content", "")) for r in records if r.get("category") == "sleep")
    exercise_total = sum(parse_exercise_minutes(r.get("content", "")) for r in records if r.get("category") == "exercise")

    def pct(v, t):
        return min(round(v / t * 100), 100) if t else 0

    return {
        "water": {"total": round(water_total), "target": round(water_target), "percent": pct(water_total, water_target), "unit": "ml"},
        "sleep": {"total": round(sleep_total, 1), "target": round(sleep_target, 1), "percent": pct(sleep_total, sleep_target), "unit": "小时"},
        "exercise": {"total": round(exercise_total), "target": round(exercise_target), "percent": pct(exercise_total, exercise_target), "unit": "分钟"},
    }


def build_alerts(goals: dict, records: list[dict], now: datetime) -> list[str]:
    """基于目标进度 + 时间，生成温柔的主动提醒（对应开发宪法第 4 条）。"""
    alerts = []
    hour = now.hour + now.minute / 60.0

    # 饮水不足
    w = goals["water"]
    if w["total"] < w["target"]:
        remain = w["target"] - w["total"]
        alerts.append(f"💧 今天才喝了 {w['total']}ml，离目标还差 {remain}ml，记得补补水哦～")

    # 运动不足
    e = goals["exercise"]
    if e["total"] < e["target"]:
        alerts.append(f"🏃 今天运动了 {e['total']} 分钟，目标 {e['target']} 分钟，找机会动一动吧～")

    # 睡眠不足（仅在已记录睡眠时提醒）
    s = goals["sleep"]
    if 0 < s["total"] < s["target"]:
        alerts.append(f"😴 只睡了 {s['total']} 小时，比目标 {s['target']} 小时少了点，今晚早点休息～")

    # 熬夜：深夜且今天还没有睡眠记录
    has_sleep = any(r.get("category") == "sleep" for r in records)
    if (hour >= 23 or hour < 5) and not has_sleep:
        alerts.append("🌙 已经很晚啦，还没记录睡眠，早点休息对身体好哦～")

    # 久坐：白天清醒时段，距最近一次运动已超过 2 小时
    if 8 <= hour <= 21:
        ex_secs = [t for t in (_to_seconds(r.get("timestamp", "")) for r in records if r.get("category") == "exercise") if t is not None]
        now_sec = hour * 3600
        if ex_secs and now_sec - max(ex_secs) > 2 * 3600:
            alerts.append("🪑 距上次运动已经坐了 2 小时以上啦，站起来伸展一下吧～")

    # 饮食不规律：基于三餐时间窗判断漏餐，以及深夜进食
    diet_hours = sorted(
        t / 3600.0 for t in (_to_seconds(r.get("timestamp", "")) for r in records if r.get("category") == "diet") if t is not None
    )
    meal_windows = [("早餐", 6, 10), ("午餐", 11, 14), ("晚餐", 17, 21)]
    missing = [
        name for name, s, e in meal_windows
        if hour > e and not any(s - 1 <= h <= e + 1 for h in diet_hours)
    ]
    if missing:
        alerts.append("🍽️ " + "、".join(missing) + "好像没记录到进食哦，尽量三餐规律，别饿着自己～")
    if any(h >= 22 or h < 5 for h in diet_hours):
        alerts.append("🌙 发现有深夜进食的记录呢，睡前两小时尽量少吃喝，肠胃和睡眠都会更轻松～")

    return alerts


def compute_weekly(records: list[dict], profile: dict, now: datetime, days: int = 7) -> dict:
    """聚合近 N 天（含今天）的饮水/睡眠/运动趋势，输出每日数值、均值、达标天数与一句温柔点评。

    复用单日解析逻辑，不依赖 AI，保证稳的可重复。旧记录无 date 字段则跳过。
    """
    from datetime import timedelta

    water_target = float(profile.get("daily_water") or 2000)
    sleep_target = float(profile.get("target_sleep") or 8)
    exercise_target = float(profile.get("daily_exercise") or 30)

    # 按日期分组
    by_date: dict[str, list[dict]] = {}
    for r in records:
        d = r.get("date", "")
        if d:
            by_date.setdefault(d, []).append(r)

    dates = [(now - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(days - 1, -1, -1)]

    day_rows = []
    for d in dates:
        recs = by_date.get(d, [])
        water = sum(parse_water_ml(r.get("content", "")) for r in recs if r.get("category") == "water")
        sleep = sum(parse_sleep_hours(r.get("content", "")) for r in recs if r.get("category") == "sleep")
        exercise = sum(parse_exercise_minutes(r.get("content", "")) for r in recs if r.get("category") == "exercise")
        has_any = bool(recs)
        day_rows.append({
            "date": d,
            "label": d[5:].replace("-", "/"),
            "water": round(water),
            "sleep": round(sleep, 1),
            "exercise": round(exercise),
            "active": has_any,
        })

    def avg(key):
        return round(sum(x[key] for x in day_rows) / days, 1)

    water_ok = sum(1 for x in day_rows if x["water"] >= water_target)
    sleep_ok = sum(1 for x in day_rows if x["sleep"] >= sleep_target)
    ex_ok = sum(1 for x in day_rows if x["exercise"] >= exercise_target)
    checkin_days = sum(1 for x in day_rows if x["active"])

    # 一句基于真实数据的温柔点评
    best = max(day_rows, key=lambda x: x["water"]) if day_rows else None
    if checkin_days == 0:
        highlight = "这一周还没有打卡记录哦，从今天开始和小眠一起记录吧～"
    else:
        highlight = (
            f"近 {days} 天你打卡了 {checkin_days} 天，日均饮水 {avg('water')}ml、睡眠 {avg('sleep')} 小时、运动 {avg('exercise')} 分钟。"
            f"饮水达标 {water_ok} 天、睡眠达标 {sleep_ok} 天、运动达标 {ex_ok} 天"
            + (f"，最棒的是 {best['label']} 喝了 {best['water']}ml！" if best and best["water"] > 0 else "，继续保持呀～")
        )

    return {
        "days": day_rows,
        "avg": {"water": avg("water"), "sleep": avg("sleep"), "exercise": avg("exercise")},
        "targets": {"water": round(water_target), "sleep": round(sleep_target, 1), "exercise": round(exercise_target)},
        "streaks": {"water": water_ok, "sleep": sleep_ok, "exercise": ex_ok},
        "checkin_days": checkin_days,
        "total_days": days,
        "highlight": highlight,
    }
