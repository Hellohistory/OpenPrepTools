import sys
import time
from functools import partial

from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QIcon, QColor, QFont, QPixmap
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QVBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QWidget,
    QMessageBox,
    QInputDialog,
    QLineEdit,
    QFileDialog,
    QDialog,
    QLabel,
    QFormLayout,
    QPushButton,
    QHBoxLayout,
    QHeaderView,
    QGraphicsDropShadowEffect
)

from secure_totp_manager_core import SecureTOTPManager, export_specific_secrets
from totp_core import TOTP


class SecretDetailsDialog(QDialog):
    """密钥详情对话框"""

    def __init__(self, parent, name, secret, save_callback):
        super().__init__(parent)
        self.setWindowTitle("🔑 查看/编辑密钥详情")
        self.setWindowIcon(QIcon("icon.png"))
        self.resize(480, 220)
        self.save_callback = save_callback

        layout = QFormLayout()
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setVerticalSpacing(16)
        layout.setHorizontalSpacing(20)

        self.name_input = QLineEdit(name)
        self.secret_input = QLineEdit(secret)
        self.secret_input.setFont(QFont("Consolas", 12))

        for input_box in (self.name_input, self.secret_input):
            effect = QGraphicsDropShadowEffect()
            effect.setBlurRadius(8)
            effect.setColor(QColor(0, 0, 0, 30))
            effect.setOffset(2, 2)
            input_box.setGraphicsEffect(effect)

        layout.addRow(QLabel("密钥名称："), self.name_input)
        layout.addRow(QLabel("密钥值："), self.secret_input)

        self.save_button = QPushButton("💾 保存")
        self.save_button.setIcon(QIcon("icons/save.png"))
        self.save_button.clicked.connect(self.save_changes)

        self.cancel_button = QPushButton("❌ 取消")
        self.cancel_button.setIcon(QIcon("icons/cancel.png"))
        self.cancel_button.clicked.connect(self.reject)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.setSpacing(12)
        btn_layout.addWidget(self.save_button)
        btn_layout.addWidget(self.cancel_button)
        layout.addRow(btn_layout)

        self.setLayout(layout)

    def save_changes(self):
        name = self.name_input.text().strip()
        secret = self.secret_input.text().strip()
        if not name or not secret:
            QMessageBox.warning(self, "错误", "密钥名称和密钥值不能为空！")
            return
        try:
            self.save_callback(name, secret)
            self.accept()
        except ValueError as e:
            QMessageBox.warning(self, "错误", str(e))


class SecureTOTPManagerGUI(QMainWindow):
    """主界面：离线 2FA 验证工具（安全版）"""

    def __init__(self, password):
        super().__init__()
        self.setWindowTitle("离线2FA验证工具（安全版）")
        self.setWindowIcon(QIcon("icon.png"))
        self.setGeometry(300, 300, 820, 560)
        self.setMinimumSize(720, 480)

        self.core = SecureTOTPManager(password)

        self.init_ui()
        self.init_menu()
        self.refresh_table()
        self.statusBar().showMessage(f"就绪 | 总密钥数: {len(self.core.get_secrets())}")

    def init_ui(self):
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels([
            "🔖 密钥名称", "🔄 当前验证码", "⏳ 剩余可用时间", "⚙️ 操作"
        ])
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setFocusPolicy(Qt.NoFocus)
        self.table.setSortingEnabled(True)
        self.table.setSelectionMode(QTableWidget.MultiSelection)

        self.table.setColumnWidth(0, 220)
        self.table.setColumnWidth(1, 160)
        self.table.setColumnWidth(2, 160)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.table.horizontalHeader().setDefaultAlignment(Qt.AlignLeft)

        self.table.cellDoubleClicked.connect(self.on_cell_double_clicked)

        layout = QVBoxLayout()
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)
        layout.addWidget(self.table)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_totps)
        self.timer.start(1000)

    def init_menu(self):
        file_menu = self.menuBar().addMenu("📁 文件")
        exp_all = QAction(QIcon("icons/export.png"), "导出所有密钥", self)
        imp = QAction(QIcon("icons/import.png"), "导入密钥", self)
        exit_act = QAction(QIcon("icons/exit.png"), "退出", self)
        exp_all.triggered.connect(self.export_secrets)
        imp.triggered.connect(self.import_secrets)
        exit_act.triggered.connect(self.close)
        file_menu.addAction(exp_all)
        file_menu.addAction(imp)
        file_menu.addSeparator()
        file_menu.addAction(exit_act)

        key_menu = self.menuBar().addMenu("🔑 密钥管理")
        add_key = QAction(QIcon("icons/add.png"), "添加密钥", self)
        add_key.triggered.connect(self.add_secret)
        key_menu.addAction(add_key)

        help_menu = self.menuBar().addMenu("❓ 帮助")
        about = QAction(QIcon("icons/about.png"), "关于", self)
        about.triggered.connect(self.show_about_dialog)
        help_menu.addAction(about)

    def on_cell_double_clicked(self, row, column):
        if column == 1:
            item = self.table.item(row, 1)
            if item:
                QApplication.clipboard().setText(item.text())
                QMessageBox.information(self, "提示", "验证码已复制到剪贴板！")

    def import_secrets(self):
        path, _ = QFileDialog.getOpenFileName(self, "导入密钥", "", "加密文件 (*.enc)")
        if not path:
            return
        pwd, ok = QInputDialog.getText(self, "输入密码", "请输入导出时设置的密码：", QLineEdit.Password)
        if ok and pwd:
            try:
                self.core.import_secrets(path, pwd)
                self.refresh_table()
                QMessageBox.information(self, "导入成功", "密钥已成功导入！")
            except Exception as e:
                QMessageBox.critical(self, "导入失败", str(e))

    def add_secret(self):
        name, ok1 = QInputDialog.getText(self, "添加密钥", "请输入密钥名称：", QLineEdit.Normal)
        if not ok1 or not name.strip():
            return
        secret, ok2 = QInputDialog.getText(self, "添加密钥", "请输入 Base32 编码的密钥：", QLineEdit.Normal)
        if not ok2 or not secret.strip():
            return
        try:
            self.core.add_secret(name.strip(), secret.strip())
            self.refresh_table()
            self.statusBar().showMessage(f"成功添加密钥：{name.strip()}", 3000)
        except ValueError as e:
            QMessageBox.critical(self, "错误", str(e))

    def remove_selected_secret(self):
        rows = self.table.selectionModel().selectedRows()
        if not rows:
            QMessageBox.warning(self, "警告", "请先选择要删除的密钥！")
            return
        confirm = QMessageBox.question(
            self, "确认删除", f"确定要删除 {len(rows)} 条密钥吗？",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirm != QMessageBox.Yes:
            return
        for idx in sorted(rows, key=lambda x: x.row(), reverse=True):
            name = self.table.item(idx.row(), 0).text()
            self.core.remove_secret(name)
        self.refresh_table()
        self.statusBar().showMessage(f"已删除 {len(rows)} 条密钥", 3000)

    def export_secrets(self):
        path, _ = QFileDialog.getSaveFileName(self, "导出密钥", "", "加密文件 (*.enc)")
        if not path:
            return
        pwd, ok = QInputDialog.getText(self, "设置密码", "请输入导出文件密码：", QLineEdit.Password)
        if ok and pwd:
            try:
                self.core.export_secrets(path, pwd)
                QMessageBox.information(self, "导出成功", f"密钥已导出到：\n{path}")
            except Exception as e:
                QMessageBox.critical(self, "导出失败", str(e))

    def refresh_table(self):
        """刷新表格并立即更新验证码与倒计时"""
        # 先关掉排序，避免插入行时导致按钮错位
        self.table.setSortingEnabled(False)
        # 清空所有行
        self.table.setRowCount(0)

        secrets = self.core.get_secrets()
        for name, secret in secrets:
            row = self.table.rowCount()
            self.table.insertRow(row)

            # ——— 名称列 ———
            name_item = QTableWidgetItem(name)
            name_item.setData(Qt.UserRole, secret)
            name_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 0, name_item)

            # ——— 验证码 / 倒计时 占位 ———
            self.table.setItem(row, 1, QTableWidgetItem())
            self.table.setItem(row, 2, QTableWidgetItem())

            # ——— 操作按钮列 ———
            btn_widget = QWidget()
            btn_layout = QHBoxLayout(btn_widget)
            btn_layout.setContentsMargins(0, 0, 0, 0)
            btn_layout.setSpacing(6)

            # “查看/编辑”
            view_btn = QPushButton("查看/编辑")
            view_btn.setIcon(QIcon("icons/edit.png"))
            view_btn.clicked.connect(
                partial(self.view_edit_secret, name, secret)
            )
            btn_layout.addWidget(view_btn)

            # “删除”
            del_btn = QPushButton("删除")
            del_btn.setIcon(QIcon("icons/remove.png"))
            del_btn.clicked.connect(
                partial(self.remove_single_secret, name)
            )
            btn_layout.addWidget(del_btn)

            # “导出”
            exp_btn = QPushButton("导出")
            exp_btn.setIcon(QIcon("icons/export_part.png"))
            exp_btn.clicked.connect(
                partial(self.export_single_secret, name, secret)
            )
            btn_layout.addWidget(exp_btn)

            btn_layout.addStretch()
            self.table.setCellWidget(row, 3, btn_widget)

        # 重新打开排序
        self.table.setSortingEnabled(True)
        # 刷新完马上填验证码＋倒计时
        self.update_totps()
        self.statusBar().showMessage(f"就绪 | 总密钥数: {len(secrets)}")

    def update_totps(self):
        now = time.time()
        remain = 30 - int(now % 30)
        for row in range(self.table.rowCount()):
            secret = self.table.item(row, 0).data(Qt.UserRole)

            # 更新验证码
            try:
                token = TOTP.get_totp_token(secret)
            except Exception:
                token = "无效密钥"

            token_item = self.table.item(row, 1)
            if token_item is None:
                token_item = QTableWidgetItem()
                self.table.setItem(row, 1, token_item)
            token_item.setText(token)
            if token != "无效密钥":
                token_item.setFont(QFont("Consolas", 14, QFont.Bold))

            # 更新剩余时间
            time_item = self.table.item(row, 2)
            if time_item is None:
                time_item = QTableWidgetItem()
                self.table.setItem(row, 2, time_item)
            time_item.setText(f"{remain} 秒")
            time_item.setFont(QFont("Arial", 11, QFont.Medium))

    def remove_single_secret(self, name):
        ans = QMessageBox.question(
            self, "确认删除", f"确定要删除密钥 '{name}' 吗？",
            QMessageBox.Yes | QMessageBox.No
        )
        if ans == QMessageBox.Yes:
            self.core.remove_secret(name)
            self.refresh_table()
            self.statusBar().showMessage(f"已删除密钥：{name}", 3000)

    def export_single_secret(self, name, secret):
        path, _ = QFileDialog.getSaveFileName(self, "导出密钥", f"{name}.enc", "加密文件 (*.enc)")
        if not path:
            return
        pwd, ok = QInputDialog.getText(self, "设置密码", f"为 '{name}' 设置密码：", QLineEdit.Password)
        if ok and pwd:
            try:
                export_specific_secrets([(name, secret)], path, pwd)
                QMessageBox.information(self, "导出成功", f"'{name}' 已导出到：\n{path}")
            except Exception as e:
                QMessageBox.critical(self, "导出失败", str(e))

    def view_edit_secret(self, name, secret):
        def save_cb(new_name, new_secret):
            self.core.remove_secret(name)
            self.core.add_secret(new_name, new_secret)
            self.refresh_table()
            self.statusBar().showMessage(f"成功更新密钥：{new_name}", 3000)

        dlg = SecretDetailsDialog(self, name, secret, save_cb)
        dlg.exec()

    def show_about_dialog(self):
        about_html = """
        <h3>离线2FA验证工具（安全版）</h3>
        <p>版本：1.1</p>
        <p>作者：Hellohistory</p>
        <ul>
          <li>完全离线运行且开源</li>
          <li>加密存储</li>
          <li>支持 TOTP 标准</li>
          <li>跨平台支持</li>
        </ul>
        <hr>
        <p>协议：核心 MIT 开源，GUI 部分 LGPL协议</p>
        <p>源码：<a href="https://github.com/Hellohistory/OpenPrepTools">GitHub</a>
         或 <a href="https://gitee.com/Hellohistory/OpenPrepTools">Gitee</a></p>
        """
        msg = QMessageBox(self)
        msg.setWindowTitle("关于")
        msg.setIconPixmap(QPixmap("icon.png").scaled(64, 64))
        msg.setTextFormat(Qt.RichText)
        msg.setText(about_html)
        msg.exec()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    pwd, ok = QInputDialog.getText(
        None,
        "密码验证",
        "请输入主密码：\n（该密码用于保护所有离线 2FA 密钥，无法找回，请务必牢记）",
        QLineEdit.Password
    )
    if ok and pwd:
        try:
            window = SecureTOTPManagerGUI(pwd)
            window.show()
            sys.exit(app.exec())
        except Exception as e:
            QMessageBox.critical(None, "致命错误", str(e))
            sys.exit(1)