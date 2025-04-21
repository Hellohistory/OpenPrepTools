# data/repository.py
"""
数据访问层：封装 SQLite 查询
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Iterable, List, Optional

from models.history_entry import HistoryEntry


class ChronologyRepository:
    """负责所有数据库读取操作"""

    def __init__(self, db_path: str | Path) -> None:
        self._conn = sqlite3.connect(str(db_path))
        self._conn.row_factory = sqlite3.Row

    @staticmethod
    def _rows_to_entries(rows: Iterable[sqlite3.Row]) -> List[HistoryEntry]:
        """
        把 sqlite3.Row 可迭代对象转换为 HistoryEntry 列表
        """
        out: List[HistoryEntry] = []
        for row in rows:
            # sqlite3.Row 无 get()，直接通过 key 访问
            period = row["时期"] if "时期" in row.keys() else ""
            regime = row["政权"] if "政权" in row.keys() else ""
            out.append(
                HistoryEntry(
                    year_ad=row["公元"],
                    ganzhi=row["干支"],
                    period=period,
                    regime=regime,
                    emperor_title=row["帝号"],
                    emperor_name=row["帝名"],
                    reign_title=row["年号"],
                    regnal_year=row["年份"],
                )
            )
        return out

    def get_entries_by_year(self, year: int) -> List[HistoryEntry]:
        """根据公元年份查询"""
        cur = self._conn.execute(
            """
            SELECT 公元, 干支, 时期, 政权, 帝号, 帝名, 年号, 年份
            FROM history_chronology
            WHERE 公元 = ?
            ORDER BY 年份
            """,
            (year,),
        )
        return self._rows_to_entries(cur.fetchall())

    def search_entries(self, keyword: str) -> List[HistoryEntry]:
        """根据关键字模糊查询：帝号、帝名、年号、时期、政权"""
        like = f"%{keyword}%"
        cur = self._conn.execute(
            """
            SELECT 公元, 干支, 时期, 政权, 帝号, 帝名, 年号, 年份
            FROM history_chronology
            WHERE 帝号 LIKE ? OR 帝名 LIKE ? OR 年号 LIKE ?
               OR 时期 LIKE ? OR 政权 LIKE ?
            ORDER BY 公元, 年份
            """,
            (like, like, like, like, like),
        )
        return self._rows_to_entries(cur.fetchall())

    def advanced_query(
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
        """多条件组合查询"""
        conditions: List[str] = []
        params: List = []

        if year_from is not None:
            conditions.append("公元 >= ?")
            params.append(year_from)
        if year_to is not None:
            conditions.append("公元 <= ?")
            params.append(year_to)
        if period:
            conditions.append("时期 LIKE ?")
            params.append(f"%{period}%")
        if regime:
            conditions.append("政权 LIKE ?")
            params.append(f"%{regime}%")
        if emperor_title:
            conditions.append("帝号 LIKE ?")
            params.append(f"%{emperor_title}%")
        if emperor_name:
            conditions.append("帝名 LIKE ?")
            params.append(f"%{emperor_name}%")
        if reign_title:
            conditions.append("年号 LIKE ?")
            params.append(f"%{reign_title}%")

        where_sql = " AND ".join(conditions) if conditions else "1"
        sql = f"""
            SELECT 公元, 干支, 时期, 政权, 帝号, 帝名, 年号, 年份
            FROM history_chronology
            WHERE {where_sql}
            ORDER BY 公元, 年份
        """
        cur = self._conn.execute(sql, tuple(params))
        return self._rows_to_entries(cur.fetchall())

    def close(self) -> None:
        """关闭数据库连接"""
        self._conn.close()
