# ui/main_window.py
"""
主窗口：支持菜单栏、深色选中、右键菜单等功能
"""

from __future__ import annotations

from typing import List
from pathlib import Path
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QCursor, QAction
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QTableWidgetItem,
    QToolTip,
    QVBoxLayout,
    QWidget,
)

import config
from data.repository import ChronologyRepository
from models.history_entry import HistoryEntry
from services.chronology_service import ChronologyService
from ui.dialogs.advanced_search_dialog import AdvancedSearchDialog
from ui.widgets.copyable_table_widget import CopyableTableWidget

# 允许查询的年份上下限
YEAR_MIN, YEAR_MAX = config.YEAR_MIN, config.YEAR_MAX

# 关于对话框里的仓库地址
GITHUB_URL = "https://github.com/yourname/yourrepo"
GITEE_URL = "https://gitee.com/yourname/yourrepo"


class MainWindow(QMainWindow):
    _headers = ["公元", "干支", "时期", "政权", "帝号", "帝名", "年号", "在位年"]
    _header_help = {
        0: "公元：甲子纪年对应的公元年份",
        1: "干支：甲子历纪年，起于公元前841年庚申",
        2: "时期：朝代，如西周、唐、明、清…",
        3: "政权：多政权并立时代划分，如战国各国、南北朝",
        4: "帝号：如太宗",
        5: "帝名：如李世民",
        6: "年号：如贞观",
        7: "在位年：年号下的序号（1=元年）",
    }

    def __init__(self, db_path: str, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(f"中华甲子历史年表")

        repo = ChronologyRepository(db_path)
        self._svc = ChronologyService(repo)

        self._create_menu()
        self._build_ui()

    def _create_menu(self) -> None:
        menubar = self.menuBar()

        file_menu = menubar.addMenu("文件")
        exit_act = QAction("退出", self)
        exit_act.setShortcut("Ctrl+Q")
        exit_act.triggered.connect(self.close)
        file_menu.addAction(exit_act)
        help_menu = menubar.addMenu("帮助")

        about_act = QAction("关于", self)
        about_act.triggered.connect(self._show_about)
        help_menu.addAction(about_act)

        thanks_act = QAction("感谢", self)
        thanks_act.triggered.connect(self._show_thanks)
        help_menu.addAction(thanks_act)

    def _show_about(self) -> None:
        """显示 关于 对话框"""
        msg = QMessageBox(self)
        msg.setWindowTitle("关于")
        msg.setTextFormat(Qt.RichText)
        msg.setText(
            f"</p>本项目开源且免费！！！！</p>"
            f"<p><b>GitHub：</b>"
            f"<a href='{GITHUB_URL}'>{GITHUB_URL}</a></p>"
            f"<p><b>Gitee：</b>"
            f"<a href='{GITEE_URL}'>{GITEE_URL}</a></p>"
        )
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec()

    def _show_thanks(self) -> None:
        msg = QMessageBox(self)
        msg.setWindowTitle("感谢")
        msg.setTextFormat(Qt.RichText)

        html = (
            "<h2>特别感谢</h2>"
            "<p>感谢 <b>经世国学馆 耕田四哥</b>！</p>"
            "<p>如果没有四哥所制作的 <i>中华甲子历史年表</i>，本项目不可能诞生。</p>"
            "<p><b>特别声明：</b>本人与经世国学馆无任何关联，仅怀揣学习之心编写此项目。</p>"
        )
        msg.setText(html)

        qr_path = Path(__file__).parent / "resources" / "经世国学馆公众号二维码.png"
        pixmap = QPixmap(str(qr_path))
        if not pixmap.isNull():
            msg.setIconPixmap(pixmap)

        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec()

    def _build_ui(self) -> None:
        root = QWidget()
        layout = QVBoxLayout(root)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        form = QHBoxLayout()
        form.setSpacing(8)
        self.year_edit = QLineEdit()
        self.year_edit.setPlaceholderText("公元年份，如 618 或 -841")
        form.addWidget(QLabel("年份："))
        form.addWidget(self.year_edit)
        year_btn = QPushButton("查询年份")
        year_btn.clicked.connect(self._on_search_year)
        form.addWidget(year_btn)

        self.key_edit = QLineEdit()
        self.key_edit.setPlaceholderText("关键字，如 李世民 / 贞观")
        form.addWidget(QLabel("关键字："))
        form.addWidget(self.key_edit)
        key_btn = QPushButton("关键字搜索")
        key_btn.clicked.connect(self._on_search_keyword)
        form.addWidget(key_btn)

        adv_btn = QPushButton("高级搜索…")
        adv_btn.clicked.connect(self._on_advanced_search)
        form.addWidget(adv_btn)
        layout.addLayout(form)

        self.table = self._create_table()
        layout.addWidget(self.table)

        self.setCentralWidget(root)

    def _create_table(self) -> CopyableTableWidget:
        tbl = CopyableTableWidget(columnCount=len(self._headers))
        tbl.setHorizontalHeaderLabels(self._headers)
        tbl.horizontalHeader().setStretchLastSection(True)
        tbl.horizontalHeader().sectionClicked.connect(self._on_header_clicked)

        tbl.setContextMenuPolicy(Qt.CustomContextMenu)
        tbl.customContextMenuRequested.connect(self._on_table_context_menu)
        return tbl

    def _on_header_clicked(self, section: int) -> None:
        if section in self._header_help:
            QToolTip.showText(QCursor.pos(), self._header_help[section], self)

    def _on_search_year(self) -> None:
        text = self.year_edit.text().strip()
        if not self._is_int(text):
            self._msg("请输入整数年份；公元前年份请加负号")
            return
        year = int(text)
        if not (YEAR_MIN <= year <= YEAR_MAX):
            self._msg(f"仅支持 {YEAR_MIN} ~ {YEAR_MAX} 年")
            return
        entries = self._svc.get_chronology_by_year(year)
        if not entries:
            self._msg(f"未找到 {year} 年记录")
        self._render(entries)

    def _on_search_keyword(self) -> None:
        kw = self.key_edit.text().strip()
        if not kw:
            self._msg("关键字不能为空")
            return
        entries = self._svc.find_entries(kw)
        if not entries:
            self._msg(f"关键字「{kw}」未匹配任何记录")
        self._render(entries)

    def _on_advanced_search(self) -> None:
        dlg = AdvancedSearchDialog(self)
        if dlg.exec() == QDialog.Accepted:
            p = dlg.get_params()
            p["year_from"] = (
                max(p["year_from"], YEAR_MIN)
                if p["year_from"] is not None
                else None
            )
            p["year_to"] = (
                min(p["year_to"], YEAR_MAX)
                if p["year_to"] is not None
                else None
            )
            entries = self._svc.advanced_search(**p)
            if not entries:
                self._msg("未找到符合条件的记录")
            self._render(entries)

    def _on_table_context_menu(self, pos: QPoint) -> None:
        """表格右键菜单：复制所选／复制整行／按此值搜索"""
        tbl = self.table
        menu = QMenu(self)

        act_copy = QAction("复制所选", self)
        act_copy.triggered.connect(tbl.copy_selection)
        menu.addAction(act_copy)

        act_row = QAction("复制整行", self)

        def copy_row() -> None:
            sel = tbl.selectedRanges()
            if not sel:
                return
            row = sel[0].topRow()
            texts = [tbl.item(row, c).text() if tbl.item(row, c) else "" for c in range(tbl.columnCount())]
            QApplication.clipboard().setText("\t".join(texts))

        act_row.triggered.connect(copy_row)
        menu.addAction(act_row)

        item = tbl.itemAt(pos)
        act_search = QAction("按此值搜索", self)
        act_search.setEnabled(item is not None)
        if item:
            def do_search() -> None:
                val = item.text()
                entries = self._svc.find_entries(val)
                if not entries:
                    self._msg(f"关键字「{val}」未匹配任何记录")
                self._render(entries)
            act_search.triggered.connect(do_search)
        menu.addAction(act_search)

        menu.exec(tbl.mapToGlobal(pos))

    def _render(self, entries: List[HistoryEntry]) -> None:
        tbl = self.table
        tbl.setRowCount(len(entries))
        for r, e in enumerate(entries):
            row = [
                str(e.year_ad),
                e.ganzhi,
                e.period,
                e.regime,
                e.emperor_title,
                e.emperor_name,
                e.reign_title,
                f"{int(e.regnal_year)}",
            ]
            for c, v in enumerate(row):
                tbl.setItem(r, c, QTableWidgetItem(v))
        tbl.resizeColumnsToContents()

    @staticmethod
    def _is_int(s: str) -> bool:
        return s.lstrip("-").isdigit()

    @staticmethod
    def _msg(text: str) -> None:
        QMessageBox.information(None, "提示", text, QMessageBox.StandardButton.Ok)
