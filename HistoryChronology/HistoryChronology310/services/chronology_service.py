# services/chronology_service.py
"""
业务层：对 ChronologyRepository 进行封装，提供给界面调用的接口
"""

from __future__ import annotations

from typing import List, Optional

from data.repository import ChronologyRepository
from models.history_entry import HistoryEntry


class ChronologyService:
    """年表业务逻辑封装"""

    def __init__(self, repo: ChronologyRepository) -> None:
        self._repo = repo

    def get_chronology_by_year(self, year: int) -> List[HistoryEntry]:
        """
        根据公元年份获取年表条目
        """
        return self._repo.get_entries_by_year(year)

    def find_entries(self, keyword: str) -> List[HistoryEntry]:
        """
        简单关键字搜索，支持干支、帝号等字段
        """
        return self._repo.search_entries(keyword)

    def advanced_search(
        self,
        *,
        year_from: Optional[int] = None,
        year_to: Optional[int] = None,
        ganzhi: str | None = None,
        period: str | None = None,
        regime: str | None = None,
        emperor_title: str | None = None,
        emperor_name: str | None = None,
        reign_title: str | None = None,
    ) -> List[HistoryEntry]:
        """
        多条件高级搜索，支持公元区间、干支、时期、政权、帝号、帝名、年号
        """
        return self._repo.advanced_query(
            year_from=year_from,
            year_to=year_to,
            ganzhi=ganzhi,
            period=period,
            regime=regime,
            emperor_title=emperor_title,
            emperor_name=emperor_name,
            reign_title=reign_title,
        )
