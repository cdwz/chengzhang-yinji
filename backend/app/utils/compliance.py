"""
成长印记 - 合规工具模块
"""
from typing import List, Tuple
import re

# 违规词汇列表
FORBIDDEN_WORDS = [
    "排名", "排行榜", "快慢班", "好差生", "打卡", 
    "每日必做", "必须完成", "重点班", "实验班"
]

# 替换词汇映射
REPLACEMENTS = {
    "排名": "个人成长进度",
    "排行榜": "班级分布概况", 
    "快慢班": "学习小组",
    "好差生": "不同学习阶段的学生",
    "打卡": "记录",
    "每日必做": "选做建议",
    "必须完成": "建议完成",
    "重点班": "特色班",
    "实验班": "特色班",
    "作业": "练习"  # 仅在家长端替换
}


def check_compliance(text: str) -> Tuple[bool, List[str]]:
    """
    检查文本是否包含违规词
    
    Args:
        text: 待检查文本
        
    Returns:
        (是否合规, 发现的违规词列表)
    """
    found = []
    for word in FORBIDDEN_WORDS:
        if word in text:
            found.append(word)
    
    return len(found) == 0, found


def sanitize_text(text: str, is_parent_view: bool = False) -> str:
    """
    替换违规词
    
    Args:
        text: 待处理文本
        is_parent_view: 是否家长端视图（家长端额外替换"作业"）
        
    Returns:
        处理后的文本
    """
    result = text
    for old, new in REPLACEMENTS.items():
        if old == "作业" and not is_parent_view:
            continue
        result = result.replace(old, new)
    
    return result


def validate_task_duration(duration: int, class_total_duration: int = 0) -> Tuple[bool, str]:
    """
    验证任务时长是否符合合规要求
    
    Args:
        duration: 当前任务建议时长（分钟）
        class_total_duration: 班级当日已有任务总时长
        
    Returns:
        (是否合规, 提示信息)
    """
    MAX_DAILY_DURATION = 60  # 每日最大建议时长
    
    if duration < 0:
        return False, "建议时长不能为负数"
    
    if duration > MAX_DAILY_DURATION:
        return False, f"单次任务建议时长不应超过{MAX_DAILY_DURATION}分钟"
    
    total = class_total_duration + duration
    if total > MAX_DAILY_DURATION:
        return False, f"今日任务总时长已达{class_total_duration}分钟，加上本次{duration}分钟将超过{MAX_DAILY_DURATION}分钟上限"
    
    return True, ""


def anonymize_statistics(total: int, count: int) -> str:
    """
    生成匿名化的统计描述
    
    Args:
        total: 总人数
        count: 符合条件人数
        
    Returns:
        匿名化的描述文本
    """
    if total == 0:
        return "暂无数据"
    
    percentage = round(count / total * 100)
    
    # 避免过于精确的数据
    if percentage < 5:
        return "少数同学"
    elif percentage < 20:
        return "约10%的同学"
    elif percentage < 30:
        return "约20%的同学"
    elif percentage < 45:
        return "约35%的同学"
    elif percentage < 55:
        return "约半数同学"
    elif percentage < 70:
        return "约60%的同学"
    elif percentage < 85:
        return "约75%的同学"
    else:
        return "绝大多数同学"


def generate_compliance_warning(violations: List[str]) -> str:
    """
    生成合规警告信息
    
    Args:
        violations: 违规词列表
        
    Returns:
        警告信息
    """
    if not violations:
        return ""
    
    words = "、".join(violations)
    return f"检测到不合规词汇：{words}。根据教育部双减政策，请使用合规表述。"
