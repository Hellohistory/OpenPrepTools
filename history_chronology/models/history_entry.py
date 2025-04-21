# models/history_entry.py
"""
领域模型：HistoryEntry
"""

from dataclasses import dataclass


@dataclass(slots=True)
class HistoryEntry:
    """历史年表条目对象"""
    year_ad: int        # 公元年份；公元前年份用负数表示
    ganzhi: str         # 干支纪年
    period: str         # 时期 / 朝代
    regime: str         # 政权
    emperor_title: str  # 帝号
    emperor_name: str   # 帝名
    reign_title: str    # 年号
    regnal_year: float  # 年号下的在位序号
