"""
食物卡路里估算模块
基于关键词匹配常见中式食物，计算摄入卡路里
"""

# 常见食物卡路里字典（每 100g/每份的大卡）
FOOD_CALORIES = {
    # 主食类
    "米饭": 116,
    "白米饭": 116,
    "面条": 110,
    "方便面": 450,  # 每包
    "泡面": 450,
    "馒头": 223,
    "包子": 250,
    "饺子": 250,
    "馄饨": 200,
    "面包": 280,
    "吐司": 280,
    "蛋糕": 350,
    "饼干": 450,
    "粥": 46,
    "小米粥": 46,
    "红薯": 86,
    "玉米": 112,
    "土豆": 76,
    
    # 蛋白质类
    "鸡蛋": 144,  # 每个约 72 大卡
    "蛋": 144,
    "牛奶": 54,  # 每 100ml
    "酸奶": 72,
    "豆浆": 30,
    "豆腐": 80,
    "鸡肉": 165,
    "牛肉": 250,
    "猪肉": 300,
    "羊肉": 200,
    "鱼": 100,
    "虾": 90,
    "蟹": 100,
    
    # 蔬菜类
    "青菜": 20,
    "白菜": 20,
    "菠菜": 23,
    "西兰花": 34,
    "番茄": 18,
    "西红柿": 18,
    "黄瓜": 16,
    "胡萝卜": 41,
    "土豆": 76,
    "茄子": 25,
    "豆角": 30,
    
    # 水果类
    "苹果": 52,
    "香蕉": 89,
    "橙子": 47,
    "橘子": 44,
    "梨": 50,
    "西瓜": 30,
    "葡萄": 45,
    "草莓": 32,
    "芒果": 60,
    
    # 饮品类
    "咖啡": 5,
    "茶": 0,
    "可乐": 43,
    "雪碧": 40,
    "果汁": 45,
    "奶茶": 80,
    "啤酒": 43,
    
    # 零食/其他
    "薯片": 530,
    "巧克力": 550,
    "糖果": 400,
    "坚果": 600,
    "花生": 560,
    "瓜子": 550,
}

# 数量关键词映射（转换为倍数）
QUANTITY_KEYWORDS = {
    "一碗": 1.5,
    "一杯": 1,
    "一瓶": 2,
    "一包": 1,
    "一个": 1,
    "两个": 2,
    "三个": 3,
    "四个": 4,
    "五个": 5,
    "半碗": 0.75,
    "半杯": 0.5,
    "半包": 0.5,
    "半个": 0.5,
}


def estimate_calories(content: str) -> int:
    """
    根据食物内容估算卡路里
    
    Args:
        content: 食物描述，如"午饭方便面一包，鸡蛋两个"
    
    Returns:
        估算的卡路里（大卡）
    """
    if not content:
        return 0
    
    import re
    total_calories = 0
    content_lower = content.lower()
    
    # 找出所有匹配的食物，按名称长度降序排列（优先匹配长名称，避免"鸡蛋"和"蛋"重复）
    matched_foods = []
    for food, calories in FOOD_CALORIES.items():
        if food in content_lower:
            matched_foods.append((food, calories))
    
    # 按名称长度降序排列，优先匹配长关键词
    matched_foods.sort(key=lambda x: len(x[0]), reverse=True)
    
    # 过滤掉被更长关键词覆盖的短匹配
    # 例如："鸡蛋"已匹配时，跳过"蛋"
    filtered = []
    consumed_spans = []  # 已匹配的文本区间
    for food, calories in matched_foods:
        # 找到 food 在 content 中的位置
        idx = content_lower.find(food)
        if idx >= 0:
            span = (idx, idx + len(food))
            # 检查这个 span 是否已被更长的匹配覆盖
            already_covered = False
            for cs, ce in consumed_spans:
                if span[0] >= cs and span[1] <= ce:
                    already_covered = True
                    break
            if not already_covered:
                filtered.append((food, calories))
                consumed_spans.append(span)
    
    # 计算卡路里
    for food, calories in filtered:
        quantity = 1.0
        # 检查是否有数量词
        for qty_keyword, qty_multiplier in QUANTITY_KEYWORDS.items():
            if qty_keyword in content_lower:
                quantity = qty_multiplier
                break
        
        # 按个算的食物，提取数字
        if "个" in content_lower:
            match = re.search(r'(\d+)\s*个', content_lower)
            if match:
                quantity = int(match.group(1))
            elif "两个" in content_lower:
                quantity = 2
            elif "三个" in content_lower:
                quantity = 3
        
        total_calories += calories * quantity
    
    return round(total_calories)


def get_calorie_level(calories: int) -> str:
    """
    根据卡路里给出评价
    
    Args:
        calories: 卡路里数值
    
    Returns:
        评价文本
    """
    if calories == 0:
        return "还没记录饮食哦"
    elif calories < 300:
        return "吃得有点少呢"
    elif calories < 500:
        return "摄入量适中"
    elif calories < 800:
        return "营养不错哦"
    else:
        return "今天吃得有点多呢"
