"""
主窗口：支持菜单栏、主题切换、退出、关于、感谢、深色选中、右键菜单等功能
使用 PySide2 代替 PySide6
"""

from __future__ import annotations

from pathlib import Path
from typing import List

from PySide2.QtCore import Qt, QPoint, QSettings
from PySide2.QtGui import QCursor
from PySide2.QtWidgets import (
    QApplication,
    QAction,
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
    QDialog,
    QAbstractItemView,
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
GITHUB_URL = "https://github.com/Hellohistory/OpenPrepTools"
GITEE_URL = "https://gitee.com/Hellohistory/OpenPrepTools"


class MainWindow(QMainWindow):
    """中华甲子历史年表 v2 主窗口"""

    def __init__(self, db_path: str, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("中华甲子历史年表")

        # 初始化设置存储，用于记住用户上次选择的主题
        self.settings = QSettings("Hellohistory", "OpenPrepTools")

        # 数据层与业务层初始化
        repo = ChronologyRepository(db_path)
        self._svc = ChronologyService(repo)

        # 构建菜单栏和主界面
        self._create_menu()
        self._build_ui()

        # 启动时从设置中加载上次主题，如果不存在则使用浅色主题
        theme_path_str = self.settings.value("theme", str(config.LIGHT_STYLE_QSS))
        theme_path = Path(theme_path_str)
        self._apply_theme(theme_path)

    def _create_menu(self) -> None:
        """创建菜单栏：文件、视图、帮助"""
        menubar = self.menuBar()

        # 文件菜单：退出
        file_menu = menubar.addMenu("文件")
        exit_act = QAction("退出", self)
        exit_act.setShortcut("Ctrl+Q")
        exit_act.triggered.connect(self.close)
        file_menu.addAction(exit_act)

        # 视图菜单：主题切换
        view_menu = menubar.addMenu("界面主题")
        themes = [
            ("浅色主题", config.LIGHT_STYLE_QSS),
            ("黑暗主题", config.DARK_STYLE_QSS),
            ("蓝色主题", config.BLUE_STYLE_QSS),
            ("绿色主题", config.GREEN_STYLE_QSS),
            ("橙色主题", config.ORANGE_STYLE_QSS),
            ("高对比主题", config.HIGHCONTRAST_STYLE_QSS),
            ("Solarized 主题", config.SOLARIZED_STYLE_QSS),
        ]
        for name, qss_path in themes:
            act = QAction(name, self)
            act.triggered.connect(lambda checked=False, p=qss_path: self._apply_theme(p))
            view_menu.addAction(act)

        # 帮助菜单：关于、感谢
        help_menu = menubar.addMenu("帮助")
        about_act = QAction("关于", self)
        about_act.triggered.connect(self._show_about)
        help_menu.addAction(about_act)

        thanks_act = QAction("感谢", self)
        thanks_act.triggered.connect(self._show_thanks)
        help_menu.addAction(thanks_act)

    def _apply_theme(self, qss_path: Path) -> None:
        """
        应用指定的 QSS 样式表，强制使用 Fusion 样式以避免系统主题干扰
        并将所选主题保存到设置，下次启动时自动加载
        :param qss_path: 样式表文件路径
        """
        app = QApplication.instance()
        app.setStyle("Fusion")
        if qss_path.exists():
            app.setStyleSheet(qss_path.read_text(encoding="utf-8"))
            self.settings.setValue("theme", str(qss_path))
        else:
            print(f"警告：未找到主题文件 {qss_path}")

    def _show_about(self) -> None:
        """显示‘关于’对话框，包含仓库链接"""
        msg = QMessageBox(self)
        msg.setWindowTitle("关于")
        msg.setTextFormat(Qt.RichText)
        msg.setText(
            f"<p><b>作者：</b>Hellohistory</p>"
            f"<p><b>版本号：</b>v1.3</p>"
            f"<p><b>GitHub：</b>"
            f"<a href='{GITHUB_URL}'>{GITHUB_URL}</a></p>"
            f"<p><b>Gitee：</b>"
            f"<a href='{GITEE_URL}'>{GITEE_URL}</a></p>"
        )
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()

    def _show_thanks(self) -> None:
        """显示‘感谢’对话框，展示致谢文案及公众号二维码"""
        msg = QMessageBox(self)
        msg.setWindowTitle("感谢")
        msg.setTextFormat(Qt.RichText)
        html = (
            "<h2>特别感谢</h2>"
            "<p>感谢 <b>经世国学馆 耕田四哥</b>！</p>"
            "<p>如果没有四哥所制作的 <i>中华甲子历史年表</i>，本项目不可能诞生。</p>"
            "<p><b>特别声明：</b>本人与经世国学馆无任何关联，仅怀揣学习之心编写此项目。</p>"
        )
        msg.setText(html)
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()

    def _build_ui(self) -> None:
        """构建查询栏和结果表格"""
        root = QWidget()
        layout = QVBoxLayout(root)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        # 顶部查询栏
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

        # 结果表格
        self.table = self._create_table()
        layout.addWidget(self.table)

        self.setCentralWidget(root)

    def _create_table(self) -> CopyableTableWidget:
        """初始化表格，设置表头、只读模式和右键菜单策略"""
        tbl = CopyableTableWidget(columnCount=8)
        tbl.setEditTriggers(QAbstractItemView.NoEditTriggers)
        tbl.setHorizontalHeaderLabels([
            "公元", "干支", "时期", "政权", "帝号", "帝名", "年号", "在位年"
        ])
        tbl.horizontalHeader().setStretchLastSection(True)
        tbl.horizontalHeader().sectionClicked.connect(self._on_header_clicked)

        tbl.setContextMenuPolicy(Qt.CustomContextMenu)
        tbl.customContextMenuRequested.connect(self._on_table_context_menu)
        return tbl

    def _on_header_clicked(self, section: int) -> None:  # noqa: D102
        help_map = {
            0: "公元：甲子纪年对应的公元年份",
            1: "干支：甲子历纪年，起于公元前841年庚申",
            2: "时期：朝代，如西周、唐、明、清…",
            3: "政权：多政权并立时代划分，如战国各国、南北朝",
            4: "帝号：如太宗",
            5: "帝名：如李世民",
            6: "年号：如贞观",
            7: "在位年：年号下的序号（1=元年）",
        }
        if section in help_map:
            QToolTip.showText(QCursor.pos(), help_map[section], self)

    def _on_search_year(self) -> None:  # noqa: D102
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

    def _on_search_keyword(self) -> None:  # noqa: D102
        kw = self.key_edit.text().strip()
        if not kw:
            self._msg("关键字不能为空")
            return
        entries = self._svc.find_entries(kw)
        if not entries:
            self._msg(f"关键字「{kw}」未匹配任何记录")
        self._render(entries)

    def _on_advanced_search(self) -> None:  # noqa: D102
        dlg = AdvancedSearchDialog(self)
        if dlg.exec_() == QDialog.Accepted:
            params = dlg.get_params()
            params["year_from"] = (
                max(params["year_from"], YEAR_MIN)
                if params["year_from"] is not None
                else None
            )
            params["year_to"] = (
                min(params["year_to"], YEAR_MAX)
                if params["year_to"] is not None
                else None
            )
            entries = self._svc.advanced_search(**params)
            if not entries:
                self._msg("未找到符合条件的记录")
            self._render(entries)

    def _on_table_context_menu(self, pos: QPoint) -> None:
        """表格右键菜单：复制所选、复制整行、按此值搜索"""
        tbl = self.table
        menu = QMenu(self)

        # 复制所选
        copy_sel = QAction("复制所选", self)
        copy_sel.triggered.connect(tbl.copy_selection)
        menu.addAction(copy_sel)

        # 复制整行
        copy_row = QAction("复制整行", self)

        def _copy_row():
            sel = tbl.selectedRanges()
            if not sel:
                return
            row = sel[0].topRow()
            texts = [
                tbl.item(row, c).text() if tbl.item(row, c) else ""
                for c in range(tbl.columnCount())
            ]
            QApplication.clipboard().setText("\t".join(texts))

        copy_row.triggered.connect(_copy_row)
        menu.addAction(copy_row)

        # 按此值搜索
        search_val = QAction("按此值搜索", self)
        item = tbl.itemAt(pos)
        search_val.setEnabled(item is not None)
        if item:
            def _search_item():
                val = item.text()
                entries = self._svc.find_entries(val)
                if not entries:
                    self._msg(f"关键字「{val}」未匹配任何记录")
                self._render(entries)

            search_val.triggered.connect(_search_item)
        menu.addAction(search_val)

        # PySide2 下使用 exec_() 弹出菜单
        menu.exec_(tbl.mapToGlobal(pos))

    def _render(self, entries: List[HistoryEntry]) -> None:
        """将查询结果渲染到表格中"""
        tbl = self.table
        tbl.setRowCount(len(entries))
        for r, e in enumerate(entries):
            # 年号顺序可能为 None，这里要兼容
            regnal_year_str = str(int(e.regnal_year)) if e.regnal_year is not None else ""
            row = [
                str(e.year_ad),
                e.ganzhi or "",
                e.period or "",
                e.regime or "",
                e.emperor_title or "",
                e.emperor_name or "",
                e.reign_title or "",
                regnal_year_str,
            ]
            for c, v in enumerate(row):
                tbl.setItem(r, c, QTableWidgetItem(v))
        tbl.resizeColumnsToContents()

    @staticmethod
    def _is_int(s: str) -> bool:  # noqa: D102
        """判断字符串是否为整数（可带负号）"""
        return s.lstrip("-").isdigit()

    @staticmethod
    def _msg(text: str) -> None:  # noqa: D102
        """弹出信息对话框"""
        QMessageBox.information(None, "提示", text, QMessageBox.StandardButton.Ok)
