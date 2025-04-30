"""
高级搜索对话框：多条件组合，年份区间由 config 控制
使用 PySide2 代替 PySide6
"""

from __future__ import annotations

from typing import Optional

from PySide2.QtWidgets import (
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
)

import config

# 从 config 中读取年份边界
YEAR_MIN, YEAR_MAX = config.YEAR_MIN, config.YEAR_MAX


class AdvancedSearchDialog(QDialog):
    """组合条件输入对话框"""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("高级搜索")
        self.setModal(True)

        form_layout = QFormLayout()

        # — 年份区间 —
        self.year_from = QSpinBox()
        self.year_from.setRange(YEAR_MIN, YEAR_MAX)
        self.year_from.setSpecialValueText("不限")
        self.year_from.setValue(self.year_from.minimum())

        self.year_to = QSpinBox()
        self.year_to.setRange(YEAR_MIN, YEAR_MAX)
        self.year_to.setSpecialValueText("不限")
        self.year_to.setValue(self.year_to.minimum())

        year_layout = QHBoxLayout()
        year_layout.addWidget(self.year_from)
        year_layout.addWidget(QLabel(" — "))
        year_layout.addWidget(self.year_to)
        form_layout.addRow("公元区间：", year_layout)

        # — 干支关键字 —
        self.ganzhi = QLineEdit()
        form_layout.addRow("干支：", self.ganzhi)

        # — 文本条件 —
        self.period = QLineEdit()
        self.regime = QLineEdit()
        self.emperor_title = QLineEdit()
        self.emperor_name = QLineEdit()
        self.reign_title = QLineEdit()

        form_layout.addRow("时期：", self.period)
        form_layout.addRow("政权：", self.regime)
        form_layout.addRow("帝号：", self.emperor_title)
        form_layout.addRow("帝名：", self.emperor_name)
        form_layout.addRow("年号：", self.reign_title)

        # — 按钮 —
        btn_layout = QHBoxLayout()
        ok_btn = QPushButton("搜索")
        ok_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addStretch(1)
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)

        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.addLayout(form_layout)
        main_layout.addLayout(btn_layout)

    def get_params(self) -> dict:
        """
        获取用户输入的参数，spinBox 如为最小值则视为 None
        """

        def spin_val(spin: QSpinBox) -> Optional[int]:
            return None if spin.value() == spin.minimum() else spin.value()

        def text_or_none(edit: QLineEdit) -> Optional[str]:
            t = edit.text().strip()
            return t or None

        return {
            "year_from": spin_val(self.year_from),
            "year_to": spin_val(self.year_to),
            "ganzhi": text_or_none(self.ganzhi),
            "period": text_or_none(self.period),
            "regime": text_or_none(self.regime),
            "emperor_title": text_or_none(self.emperor_title),
            "emperor_name": text_or_none(self.emperor_name),
            "reign_title": text_or_none(self.reign_title),
        }
