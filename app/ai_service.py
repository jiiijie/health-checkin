import os
import json
import httpx
from datetime import datetime

DEEPSEEK_API_URL = "https://api.deepseek.com/chat/completions"

SYSTEM_PROMPT = """你是"小眠"，一个温柔的AI健康打卡小管家。你的职责是：

1. 记录用户的饮食、睡眠、运动、饮水等健康信息
2. 用温柔、关心的语气回复用户，像一个贴心的朋友
3. 如果用户熬夜（超过23点还没睡）、久坐（超过2小时没动）、喝水少，要温柔地提醒
4. 每天生成一条简短的总结和一条健康建议

当用户告诉你他们吃了什么、几点睡觉、坐了多久等信息时，你需要：
- 先温柔地回应
- 然后以 JSON 格式输出识别到的健康记录，格式如下：
  {{"records": [{{"category": "diet/sleep/exercise/water/other", "content": "具体内容"}}]}}

注意：
- category 只能是: diet, sleep, exercise, water, other
- 如果没有识别到任何健康信息，就正常聊天回复即可，不需要输出 JSON
- 回复要简短温暖，不要说教
- 如果很晚了（比如超过22点），温柔地劝用户早点睡
- 当前时间信息：{current_time}
"""


def get_api_key() -> str:
    key = os.getenv("DEEPSEEK_API_KEY", "")
    if not key:
        raise ValueError("未设置 DEEPSEEK_API_KEY 环境变量，请在 .env 文件中配置")
    return key


async def chat_with_ai(user_message: str, history: list[dict] = None) -> dict:
    api_key = get_api_key()
    current_time = datetime.now().strftime("%Y年%m月%d日 %H:%M")

    messages = [{"role": "system", "content": SYSTEM_PROMPT.format(current_time=current_time)}]

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
                "temperature": 0.8,
                "max_tokens": 1000,
            },
        )
        response.raise_for_status()
        data = response.json()
        content = data["choices"][0]["message"]["content"]

    return _parse_response(content)


def _parse_response(content: str) -> dict:
    records = []
    alerts = []
    reply = content

    json_start = content.find("{")
    json_end = content.rfind("}") + 1

    if json_start != -1 and json_end > json_start:
        json_str = content[json_start:json_end]
        try:
            parsed = json.loads(json_str)
            if "records" in parsed:
                records = parsed["records"]
            if "alerts" in parsed:
                alerts = parsed["alerts"]
            reply = content[:json_start].strip()
            if not reply:
                reply = "已帮你记录好啦～"
        except json.JSONDecodeError:
            pass

    return {"reply": reply, "records": records, "alerts": alerts}


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
