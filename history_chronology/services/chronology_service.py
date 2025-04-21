# services/chronology_service.py
"""
业务逻辑层：组合统一出口
"""

from typing import List, Optional

from data.repository import ChronologyRepository
from models.history_entry import HistoryEntry


class ChronologyService:
    def __init__(self, repo: ChronologyRepository) -> None:
        self._repo = repo

    def get_chronology_by_year(self, year: int) -> List[HistoryEntry]:
        """按年份查询"""
        return self._repo.get_entries_by_year(year)

    def find_entries(self, keyword: str) -> List[HistoryEntry]:
        """关键字搜索"""
        return self._repo.search_entries(keyword)

    def advanced_search(
        self,
        *,
        year_from: Optional[int] = None,
        year_to: Optional[int] = None,
        period: str | None = None,
        regime: str | None = None,
        emperor_title: str | None = None,
        emperor_name: str | None = None,
        reign_title: str | None = None,
    ) -> List[HistoryEntry]:
        return self._repo.advanced_query(
            year_from=year_from,
            year_to=year_to,
            period=period,
            regime=regime,
            emperor_title=emperor_title,
            emperor_name=emperor_name,
            reign_title=reign_title,
        )
