# ui/widgets/timeline_widget.py
"""
TimelineWidget：提示文本加入 period、regime
"""

from __future__ import annotations

from typing import List

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import (
    QGraphicsEllipseItem,
    QGraphicsItem,
    QGraphicsScene,
    QGraphicsTextItem,
    QGraphicsView,
)

from models.history_entry import HistoryEntry


class TimelineWidget(QGraphicsView):
    _year_span = 10

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)
        self._entries: List[HistoryEntry] = []

    # ---------- API ----------
    def set_entries(self, entries: List[HistoryEntry]) -> None:
        self._entries = entries
        self._rebuild_scene()

    def _rebuild_scene(self) -> None:
        self._scene.clear()
        if not self._entries:
            self._scene.setSceneRect(QRectF(0, 0, 1, 1))
            return

        min_y = min(e.year_ad for e in self._entries)
        max_y = max(e.year_ad for e in self._entries)
        w = (max_y - min_y + 1) * self._year_span
        self._scene.setSceneRect(0, 0, w, 120)

        base_pen = QPen(QColor("#888"), 2)
        self._scene.addLine(0, 60, w, 60, base_pen)

        for e in self._entries:
            x = (e.year_ad - min_y) * self._year_span
            self._create_node(x, e)

    def _create_node(self, x: float, e: HistoryEntry) -> None:
        r = 4
        dot: QGraphicsEllipseItem = self._scene.addEllipse(
            QRectF(x - r, 60 - r, r * 2, r * 2),
            QPen(Qt.PenStyle.NoPen),
            QColor("#1e88e5"),
        )
        dot.setToolTip(self._tooltip(e))
        dot.setZValue(1)

        txt: QGraphicsTextItem = self._scene.addText(
            f"{e.reign_title}{int(e.regnal_year)}"
        )
        txt.setDefaultTextColor(QColor("#333"))
        txt.setPos(QPointF(x - txt.boundingRect().width() / 2, 30))
        txt.setToolTip(self._tooltip(e))
        txt.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)

    @staticmethod
    def _tooltip(e: HistoryEntry) -> str:
        return (
            f"{e.year_ad}（{e.ganzhi}）\n"
            f"{e.period}·{e.regime}\n"
            f"{e.emperor_title}·{e.emperor_name}\n"
            f"{e.reign_title} 第 {int(e.regnal_year)} 年"
        )
