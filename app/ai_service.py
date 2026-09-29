import os
import json
import httpx
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

DEEPSEEK_API_URL = "https://api.deepseek.com/chat/completions"

SYSTEM_PROMPT = """你是"小眠"，一个温柔的AI健康打卡小管家。你的职责是：

1. 记录用户的饮食、睡眠、运动、饮水等健康信息
2. 用温柔、关心的语气回复用户，像一个贴心的朋友
3. 如果用户熬夜（超过23点还没睡）、久坐（超过2小时没动）、喝水少，要温柔地提醒
4. 每天生成一条简短的总结和一条健康建议

【核心规则 - 必须严格遵守】
只要用户消息中包含任何健康相关信息（吃了什么、喝了什么、睡了多久、运动了等），你的回复必须包含两部分：
第一部分：温柔简短的回应文字
第二部分：紧接着输出一个 JSON 块记录信息，格式如下：
{{"records": [{{"category": "diet/sleep/exercise/water/other", "content": "具体内容"}}]}}

没有输出 JSON = 没有记录。即使内容和之前完全相同，也必须每次都输出 JSON 记录。

当用户在对话中透露了个人基本信息（如身高、体重、年龄、性别、腰围等），
请在 JSON 中额外输出 profile_update 字段来更新档案：
  {{"records": [...], "profile_update": {{"height": 170, "weight": 65}}}}

profile_update 可用字段：nickname, gender, age, height, weight, waist, arm, leg, chest, target_weight, daily_water, daily_exercise, target_sleep
只输出用户明确提到的字段，不要猜测。

其他注意事项：
- category 只能是: diet, sleep, exercise, water, other
- 如果用户说的内容与健康完全无关（如问好、闲聊），则正常聊天回复，不需要输出 JSON
- 【重要】当用户是在“请求总结/回顾今天/要建议/询问已有哪些记录”等元操作时，绝不要输出 records JSON！这类请求本身不是健康事件，只需根据今日记录直接用文字回答
- 回复要简短温暖，不要说教
- 如果很晚了（比如超过22点），温柔地劝用户早点睡
- 当前时间信息：{current_time}
- 【重要】每次用户说的健康相关事件都是独立记录，即使内容和之前完全相同也必须分别记录，绝对不要自行去重或拒绝记录！但总结/查询类请求不属于健康事件

用户当前档案（已知的信息，不要重复询问）：
{profile_info}

用户今天的打卡记录（已保存的真实数据。当用户要求总结/回顾今天，或询问今天做了什么时，必须基于以下记录如实回答，绝不能说"没收到记录"）：
{records_info}
"""


def get_api_key() -> str:
    key = os.getenv("DEEPSEEK_API_KEY", "")
    if not key:
        raise ValueError("未设置 DEEPSEEK_API_KEY 环境变量，请在 .env 文件中配置")
    return key


async def chat_with_ai(user_message: str, history: list[dict] = None, profile: dict = None, records: list[dict] = None) -> dict:
    api_key = get_api_key()
    current_time = datetime.now().strftime("%Y年%m月%d日 %H:%M")

    # 构建档案信息字符串
    profile_info = "暂无档案信息"
    if profile:
        parts = []
        field_labels = {
            "nickname": "昵称", "gender": "性别", "age": "年龄",
            "height": "身高cm", "weight": "体重kg",
            "waist": "腰围cm", "arm": "臂围cm", "leg": "腿围cm", "chest": "胸围cm",
            "target_weight": "目标体重kg", "daily_water": "每日饮水ml",
            "daily_exercise": "每日运动分钟", "target_sleep": "目标睡眠小时",
        }
        for key, label in field_labels.items():
            if profile.get(key) is not None:
                parts.append(f"{label}={profile[key]}")
        if parts:
            profile_info = "、".join(parts)

    # 构建今日记录上下文
    records_info = "今天暂无打卡记录"
    if records:
        cat_labels = {"diet": "🍽️饮食", "sleep": "😴睡眠", "exercise": "🏃运动", "water": "💧饮水", "other": "📝其他"}
        parts = [f"- [{cat_labels.get(r.get('category'), r.get('category'))} {r.get('timestamp', '')}] {r.get('content')}" for r in records]
        records_info = "\n".join(parts)

    messages = [{"role": "system", "content": SYSTEM_PROMPT.format(current_time=current_time, profile_info=profile_info, records_info=records_info)}]

    if history:
        messages.extend(history[-10:])

    messages.append({"role": "user", "content": user_message})

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            DEEPSEEK_API_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": "deepseek-chat",
                "messages": messages,
                "temperature": 0.5,
                "max_tokens": 1000,
            },
        )
        response.raise_for_status()
        data = response.json()
        content = data["choices"][0]["message"]["content"]

    print(f"[AI Response] {content[:500]}")
    return _parse_response(content)


def _parse_response(content: str) -> dict:
    records = []
    alerts = []
    profile_update = {}
    reply = content

    # 更健壮的 JSON 提取：找到包含 "records" 的 JSON 块
    json_str = _extract_json_with_key(content, "records")
    if not json_str:
        # 尝试找 profile_update
        json_str = _extract_json_with_key(content, "profile_update")

    if json_str:
        try:
            parsed = json.loads(json_str)
            if "records" in parsed:
                records = parsed["records"]
            if "alerts" in parsed:
                alerts = parsed["alerts"]
            if "profile_update" in parsed and isinstance(parsed["profile_update"], dict):
                profile_update = parsed["profile_update"]
            # 回复文字 = JSON 之前的部分
            json_pos = content.find(json_str)
            reply = content[:json_pos].strip()
            if not reply:
                reply = "已帮你记录好啦～"
        except json.JSONDecodeError:
            pass

    return {"reply": reply, "records": records, "alerts": alerts, "profile_update": profile_update}


def _extract_json_with_key(text: str, key: str) -> str | None:
    """从文本中找到包含指定 key 的最外层 JSON 对象，用花括号计数匹配"""
    # 从后往前找 "key" 出现的位置，然后向前找到最近的 {
    search_pattern = f'"{key}"'
    idx = text.rfind(search_pattern)
    if idx == -1:
        return None

    # 向前找到这个 JSON 对象的起始 {
    start = text.rfind("{", 0, idx)
    if start == -1:
        return None

    # 用花括号计数找到匹配的 }
    depth = 0
    for i in range(start, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return text[start:i + 1]

    return None


async def generate_summary(records: list[dict]) -> dict:
    api_key = get_api_key()

    records_text = "\n".join(
        [f"- [{r['category']}] {r['content']}（{r['timestamp']}）" for r in records]
    )

    prompt = f"""以下是用户今天的健康打卡记录：
{records_text}

请生成：
1. 一条简短的今日总结（50字以内，温柔语气）
2. 一条健康建议（50字以内，实用为主）

用 JSON 格式返回：{{"summary": "总结内容", "suggestion": "建议内容"}}"""

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            DEEPSEEK_API_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": "deepseek-chat",
                "messages": [
                    {"role": "system", "content": "你是小眠，温柔的AI健康管家。"},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.7,
                "max_tokens": 500,
            },
        )
        response.raise_for_status()
        data = response.json()
        content = data["choices"][0]["message"]["content"]

    json_start = content.find("{")
    json_end = content.rfind("}") + 1
    if json_start != -1 and json_end > json_start:
        try:
            return json.loads(content[json_start:json_end])
        except json.JSONDecodeError:
            pass

    return {"summary": "今天也要好好照顾自己哦～", "suggestion": "记得多喝水，早点休息～"}
