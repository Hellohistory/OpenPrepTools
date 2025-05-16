# data/repository.py
"""
数据访问层：封装 SQLite 查询，支持简繁体混合检索
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Iterable, List, Optional, Set

from opencc import OpenCC

from models.history_entry import HistoryEntry


class ChronologyRepository:
    """负责所有数据库读取操作，支持简繁体互转查询"""

    def __init__(self, db_path: str | Path) -> None:
        # 初始化 SQLite 连接
        self._conn = sqlite3.connect(str(db_path))
        self._conn.row_factory = sqlite3.Row
        # 初始化简繁转换器
        self._cc_s2t = OpenCC('s2t')  # 简体 -> 繁体
        self._cc_t2s = OpenCC('t2s')  # 繁体 -> 简体

    @staticmethod
    def _rows_to_entries(rows: Iterable[sqlite3.Row]) -> List[HistoryEntry]:
        """
        将 sqlite3.Row 可迭代对象转换为 HistoryEntry 列表
        """
        out: List[HistoryEntry] = []
        for row in rows:
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

    def _generate_variants(self, text: str) -> Set[str]:
        """
        生成关键词的简／繁体两种形式，去重后返回
        """
        variants: Set[str] = {text}
        # 双向转换，保证简繁都能覆盖
        variants.add(self._cc_s2t.convert(text))
        variants.add(self._cc_t2s.convert(text))
        return variants

    def _split_keyword(self, keyword: str) -> List[str]:
        """
        特殊关键词分解映射。比如“東周（春秋）”可分解为["東周", "春秋"]
        可以扩展更多映射
        """
        mapping = {
            "東周（春秋）": ["東周", "春秋"],
            "东周（春秋）": ["东周", "春秋"],
            "東周（戰國）": ["東周", "戰國"],
            "东周（战国）": ["东周", "战国"],
        }
        # 命中特殊分词直接返回分解后的列表，否则返回原关键词
        return mapping.get(keyword, [keyword])

    def get_entries_by_year(self, year: int) -> List[HistoryEntry]:
        """
        根据公元年份查询所有匹配记录
        """
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
        """
        根据关键字模糊查询，支持简繁体互转
        查询字段：干支、帝号、帝名、年号、时期、政权
        支持特殊关键词分解
        """
        # 先分解关键字
        keywords = self._split_keyword(keyword)
        all_results: List[HistoryEntry] = []
        seen_keys = set()  # 用于去重

        for key in keywords:
            variants = self._generate_variants(key)
            text_cols = ["干支", "帝号", "帝名", "年号", "时期", "政权"]
            conditions: List[str] = []
            params: List[str] = []

            for var in variants:
                like = f"%{var}%"
                for col in text_cols:
                    conditions.append(f"{col} LIKE ?")
                    params.append(like)
            where_sql = " OR ".join(conditions)
            sql = f"""
                SELECT 公元, 干支, 时期, 政权, 帝号, 帝名, 年号, 年份
                FROM history_chronology
                WHERE {where_sql}
                ORDER BY 公元, 年份
            """
            cur = self._conn.execute(sql, tuple(params))
            results = self._rows_to_entries(cur.fetchall())

            # 去重（假设year_ad + emperor_title + reign_title唯一标识一条记录）
            for entry in results:
                unique_key = (entry.year_ad, entry.ganzhi, entry.emperor_title, entry.reign_title)
                if unique_key not in seen_keys:
                    seen_keys.add(unique_key)
                    all_results.append(entry)
        return all_results

    def advanced_query(
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
        多条件组合查询，所有文本条件均支持简繁体互转
        支持字段：公元区间、干支、时期、政权、帝号、帝名、年号
        """
        conditions: List[str] = []
        params: List = []

        # 年份范围条件
        if year_from is not None:
            conditions.append("公元 >= ?")
            params.append(year_from)
        if year_to is not None:
            conditions.append("公元 <= ?")
            params.append(year_to)

        # 文本列条件，使用简繁转换
        def add_text_condition(col: str, val: str) -> None:
            for variant in self._generate_variants(val):
                conditions.append(f"{col} LIKE ?")
                params.append(f"%{variant}%")

        # 干支关键字
        if ganzhi:
            add_text_condition("干支", ganzhi)
        # 其它文本关键词
        if period:
            add_text_condition("时期", period)
        if regime:
            add_text_condition("政权", regime)
        if emperor_title:
            add_text_condition("帝号", emperor_title)
        if emperor_name:
            add_text_condition("帝名", emperor_name)
        if reign_title:
            add_text_condition("年号", reign_title)

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
        """
        关闭数据库连接
        """
        self._conn.close()
