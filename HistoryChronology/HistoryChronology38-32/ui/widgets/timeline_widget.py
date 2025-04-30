"""
TimelineWidget：提示文本加入 period、regime
使用 PySide2 代替 PySide6
"""

from __future__ import annotations

from typing import List

from PySide2.QtCore import QPointF, QRectF, Qt
from PySide2.QtGui import QColor, QPainter, QPen
from PySide2.QtWidgets import (
    QGraphicsItem,
    QGraphicsScene,
    QGraphicsView,
)

from models.history_entry import HistoryEntry


class TimelineWidget(QGraphicsView):
    """时间线控件，显示历史年表节点，并在鼠标悬停时显示详情"""

    _year_span = 10

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        # 启用抗锯齿
        self.setRenderHint(QPainter.Antialiasing)
        # 滚动条设置
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        # 场景初始化
        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)
        self._entries: List[HistoryEntry] = []

    def set_entries(self, entries: List[HistoryEntry]) -> None:
        """设置数据并重建场景"""
        self._entries = entries
        self._rebuild_scene()

    def _rebuild_scene(self) -> None:
        """根据 entries 绘制时间线和节点"""
        self._scene.clear()
        if not self._entries:
            self._scene.setSceneRect(QRectF(0, 0, 1, 1))
            return

        # 计算范围
        min_year = min(e.year_ad for e in self._entries)
        max_year = max(e.year_ad for e in self._entries)
        width = (max_year - min_year + 1) * self._year_span
        self._scene.setSceneRect(0, 0, width, 120)

        # 绘制中心基线
        base_pen = QPen(QColor("#888"), 2)
        self._scene.addLine(0, 60, width, 60, base_pen)

        # 绘制每个节点
        for entry in self._entries:
            x = (entry.year_ad - min_year) * self._year_span
            self._create_node(x, entry)

    def _create_node(self, x: float, entry: HistoryEntry) -> None:
        """绘制单个节点及文本"""
        r = 4
        # 圆点
        dot = self._scene.addEllipse(
            QRectF(x - r, 60 - r, r * 2, r * 2),
            QPen(Qt.NoPen),
            QColor("#1e88e5"),
        )
        dot.setToolTip(self._tooltip(entry))
        dot.setZValue(1)

        # 文本
        text = self._scene.addText(
            f"{entry.reign_title}{int(entry.regnal_year)}"
        )
        text.setDefaultTextColor(QColor("#333"))
        text_width = text.boundingRect().width()
        text.setPos(QPointF(x - text_width / 2, 30))
        text.setToolTip(self._tooltip(entry))
        text.setFlag(QGraphicsItem.ItemIsSelectable)

    @staticmethod
    def _tooltip(entry: HistoryEntry) -> str:
        """生成 Tooltip 文本"""
        return (
            f"{entry.year_ad}（{entry.ganzhi}）\n"
            f"{entry.period}·{entry.regime}\n"
            f"{entry.emperor_title}·{entry.emperor_name}\n"
            f"{entry.reign_title} 第 {int(entry.regnal_year)} 年"
        )
