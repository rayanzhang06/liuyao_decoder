"""文本处理工具函数"""
import re
from typing import List


def extract_chinese_chars(text: str) -> int:
    """
    统计中文字符数

    Args:
        text: 输入文本

    Returns:
        int: 中文字符数量
    """
    return sum(1 for c in text if '\u4e00' <= c <= '\u9fff')


def extract_keywords(text: str, patterns: List[str]) -> List[str]:
    """
    基于正则表达式提取关键词

    Args:
        text: 输入文本
        patterns: 正则表达式模式列表

    Returns:
        List[str]: 提取的关键词列表
    """
    keywords = []
    for pattern in patterns:
        matches = re.findall(pattern, text)
        keywords.extend(matches)
    return keywords


def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
    """
    截断文本到指定长度

    Args:
        text: 输入文本
        max_length: 最大长度
        suffix: 截断后添加的后缀

    Returns:
        str: 截断后的文本
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def clean_filename(filename: str, max_length: int = 50) -> str:
    """
    清理文件名，移除特殊字符

    Args:
        filename: 原始文件名
        max_length: 最大长度

    Returns:
        str: 清理后的文件名
    """
    # 移除文件名中的特殊字符
    safe_filename = re.sub(r'[<>:"/\\|?*]', '', filename)
    # 去除首尾空格
    safe_filename = safe_filename.strip()
    # 限制长度
    if len(safe_filename) > max_length:
        safe_filename = safe_filename[:max_length]
    return safe_filename


def estimate_tokens(text: str) -> int:
    """
    估算文本的token数量

    Args:
        text: 输入文本

    Returns:
        int: 估算的token数量
    """
    # 粗略估算：中文 1 token ≈ 0.75 个字符，英文 1 token ≈ 4 个字符
    chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
    other_chars = len(text) - chinese_chars
    return int(chinese_chars / 0.75 + other_chars / 4)


def format_timestamp(timestamp, format_str: str = '%Y-%m-%d %H:%M') -> str:
    """
    格式化时间戳

    Args:
        timestamp: datetime对象
        format_str: 格式字符串

    Returns:
        str: 格式化后的时间字符串
    """
    if timestamp is None:
        return ""
    return timestamp.strftime(format_str)
