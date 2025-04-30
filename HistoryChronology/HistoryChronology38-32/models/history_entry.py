"""
数据模型：历史条目，表示甲子年表中的一条记录
"""

from dataclasses import dataclass
from typing import ClassVar, Tuple


@dataclass
class HistoryEntry:
    """
    表示一次在位信息：
    year_ad: 公元年份
    ganzhi: 干支纪年
    period: 朝代时期
    regime: 政权
    emperor_title: 帝号
    emperor_name: 皇帝姓名
    reign_title: 年号
    regnal_year: 在位年序号
    """
    # 定义 __slots__ 以减少内存开销，模拟 dataclass(slots=True)
    __slots__: ClassVar[Tuple[str, ...]] = (
        'year_ad',
        'ganzhi',
        'period',
        'regime',
        'emperor_title',
        'emperor_name',
        'reign_title',
        'regnal_year'
    )

    year_ad: int               # 公元年份
    ganzhi: str                # 干支纪年
    period: str                # 朝代时期
    regime: str                # 政权
    emperor_title: str         # 帝号，如太宗
    emperor_name: str          # 皇帝姓名，如李世民
    reign_title: str           # 年号，如贞观
    regnal_year: float         # 在位序年，例如1.0, 2.0
