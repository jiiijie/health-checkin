"""
食物卡路里估算模块
使用 AI（DeepSeek）根据食物描述智能估算卡路里
"""
import os
import json
import re
import logging
import httpx

logger = logging.getLogger(__name__)

DEEPSEEK_API_URL = "https://api.deepseek.com/chat/completions"

CALORIE_PROMPT = """你是一个营养学专家。请根据用户描述的食物内容，估算总卡路里（大卡/kcal）。

规则：
1. 只返回一个 JSON 对象，格式为 {{"calories": 数字}}
2. 数字为整数，表示总卡路里
3. 如果无法判断或内容不是食物描述，返回 {{"calories": 0}}
4. 考虑食物的分量（如"一碗""两个""一包"等）
5. 如果是多道菜/多种食物，计算总和

示例：
- "午饭方便面一包，鸡蛋两个" → {{"calories": 594}}
- "早餐一杯牛奶，两片吐司" → {{"calories": 388}}
- "晚上吃了个苹果" → {{"calories": 52}}
- "今天喝了杯水" → {{"calories": 0}}

用户描述：{content}"""


def _get_api_key() -> str:
    key = os.getenv("DEEPSEEK_API_KEY", "")
    if not key:
        raise ValueError("未设置 DEEPSEEK_API_KEY 环境变量")
    return key


async def estimate_calories(content: str) -> int:
    """
    使用 AI 根据食物描述估算卡路里
    
    Args:
        content: 食物描述，如"午饭方便面一包，鸡蛋两个"
    
    Returns:
        估算的卡路里（大卡），AI 失败时返回 0
    """
    if not content:
        return 0
    
    try:
        api_key = _get_api_key()
        prompt = CALORIE_PROMPT.format(content=content)
        
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                DEEPSEEK_API_URL,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "deepseek-chat",
                    "messages": [
                        {"role": "system", "content": "你是营养学专家，只返回 JSON。"},
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": 0.3,
                    "max_tokens": 50,
                },
            )
            response.raise_for_status()
            data = response.json()
            ai_content = data["choices"][0]["message"]["content"]
            
            # 提取 JSON
            json_match = re.search(r'\{[^}]*"calories"\s*:\s*(\d+)[^}]*\}', ai_content)
            if json_match:
                calories = int(json_match.group(1))
                # 合理性检查：单次饮食不超过 3000 大卡
                if 0 <= calories <= 3000:
                    logger.info(f"[Calories AI] '{content}' → {calories} kcal")
                    return calories
                else:
                    logger.warning(f"[Calories AI] 异常值 {calories}，内容: '{content}'")
                    return 0
            
            logger.warning(f"[Calories AI] 无法解析 JSON: {ai_content[:100]}")
            return 0
            
    except Exception as e:
        logger.error(f"[Calories AI] 估算失败: {e}")
        return 0


def _calc_tdee(profile: dict) -> int:
    """
    用 Mifflin-St Jeor 公式计算每日总能量消耗（TDEE）
    
    Args:
        profile: 用户档案，包含 height(cm), weight(kg), age, gender
    
    Returns:
        TDEE（大卡），无法计算时返回 2200（默认值）
    """
    height = profile.get("height")
    weight = profile.get("weight")
    age = profile.get("age")
    gender = profile.get("gender", "")
    
    if not all([height, weight, age]):
        return 2200  # 默认值
    
    # Mifflin-St Jeor 公式
    if gender == "男" or gender == "male":
        bmr = 10 * weight + 6.25 * height - 5 * age + 5
    else:
        bmr = 10 * weight + 6.25 * height - 5 * age - 161
    
    # 活动系数（默认轻度活动 1.375）
    activity_factor = 1.375
    return round(bmr * activity_factor)


def get_calorie_level(calories: int, profile: dict = None) -> str:
    """
    根据卡路里和用户档案给出个性化评价
    
    Args:
        calories: 已摄入卡路里
        profile: 用户档案（可选）
    
    Returns:
        评价文本
    """
    if calories == 0:
        return "还没记录饮食哦"
    
    tdee = _calc_tdee(profile or {})
    ratio = calories / tdee  # 摄入占比
    
    if ratio < 0.3:
        return "吃得有点少呢，记得补充能量哦～"
    elif ratio < 0.6:
        return "摄入还不到一半，继续加油！"
    elif ratio < 0.85:
        return "摄入量适中，保持节奏～"
    elif ratio <= 1.1:
        return "营养不错哦，今天吃得刚刚好！"
    else:
        return "今天吃得有点多呢，注意控制哦～"
