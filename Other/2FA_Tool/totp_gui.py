import sys
import time

from PyQt5.QtCore import (
    QTimer, Qt
)
from PyQt5.QtGui import (
    QIcon, QColor, QFont, QPixmap
)
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QWidget, QMessageBox, QInputDialog, QLineEdit, QFileDialog, QDialog,
    QLabel, QFormLayout, QAction, QPushButton, QHBoxLayout, QHeaderView,
    QGraphicsDropShadowEffect
)

from secure_totp_manager_core import SecureTOTPManager
from totp_core import TOTP


class SecretDetailsDialog(QDialog):
    """密钥详情对话框"""

    def __init__(self, parent, name, secret, save_callback):
        super().__init__(parent)
        self.setWindowTitle("🔑 查看/编辑密钥详情")
        self.setWindowIcon(QIcon("icon.png"))
        self.resize(480, 220)
        self.save_callback = save_callback

        # 主布局
        layout = QFormLayout()
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setVerticalSpacing(16)
        layout.setHorizontalSpacing(20)

        # 输入框
        self.name_input = QLineEdit(name)
        self.secret_input = QLineEdit(secret)
        self.secret_input.setFont(QFont("Consolas", 12))

        # 添加阴影效果
        for input_box in [self.name_input, self.secret_input]:
            effect = QGraphicsDropShadowEffect()
            effect.setBlurRadius(8)
            effect.setColor(QColor(0, 0, 0, 30))
            effect.setOffset(2, 2)
            input_box.setGraphicsEffect(effect)

        layout.addRow(QLabel("密钥名称："), self.name_input)
        layout.addRow(QLabel("密钥值："), self.secret_input)

        # 按钮布局
        self.save_button = QPushButton("💾 保存")
        self.save_button.clicked.connect(self.save_changes)
        self.save_button.setIcon(QIcon("icons/save.png"))

        self.cancel_button = QPushButton("❌ 取消")
        self.cancel_button.clicked.connect(self.reject)
        self.cancel_button.setIcon(QIcon("icons/cancel.png"))

        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)
        button_layout.setSpacing(12)

        layout.addRow(button_layout)
        self.setLayout(layout)

    def save_changes(self):
        """保存更改"""
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
    def __init__(self, password):
        super().__init__()
        self.setWindowTitle("离线2FA验证工具（安全版）")
        self.setGeometry(300, 300, 820, 560)
        self.setWindowIcon(QIcon("icon.png"))
        self.setMinimumSize(720, 480)

        # 初始化核心逻辑
        self.core = SecureTOTPManager(password)

        # 初始化UI
        self.init_ui()

        # 初始化菜单
        self.init_menu()

        # 刷新表格
        self.refresh_table()

        # 状态栏
        self.statusBar().showMessage(f"就绪 | 总密钥数: {len(self.core.get_secrets())}")

    def init_ui(self):
        """初始化界面组件"""
        # 主表格
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["🔖 密钥名称", "🔄 当前验证码", "⏳ 剩余可用时间", "⚙️ 操作"])
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setFocusPolicy(Qt.NoFocus)
        self.table.setSortingEnabled(True)

        self.table.setSelectionMode(QTableWidget.MultiSelection)

        # 列宽设置
        self.table.setColumnWidth(0, 220)
        self.table.setColumnWidth(1, 160)
        self.table.setColumnWidth(2, 160)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.table.horizontalHeader().setDefaultAlignment(Qt.AlignLeft)

        # 主布局
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(16)
        main_layout.addWidget(self.table)

        # 中央部件
        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        # 定时器：用于定时更新验证码
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_totps)
        self.timer.start(1000)

    def import_secrets(self):
        """从加密文件导入密钥"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "导入密钥",
            "",
            "加密文件 (*.enc)",
            options=QFileDialog.DontUseNativeDialog
        )
        if file_path:
            password, ok = QInputDialog.getText(
                self,
                "输入密码",
                "请输入导出文件时设置的密码：",
                QLineEdit.Password,
                flags=Qt.Dialog | Qt.CustomizeWindowHint | Qt.WindowTitleHint
            )
            if ok and password:
                try:
                    # 调用 core 中的 import_secrets
                    self.core.import_secrets(file_path, password)
                    self.refresh_table()
                    QMessageBox.information(self, "导入成功", "密钥已成功导入！", QMessageBox.Ok)
                except Exception as e:
                    QMessageBox.critical(self, "导入失败", f"导入过程中发生错误：\n{str(e)}", QMessageBox.Ok)

    def init_menu(self):
        """初始化菜单系统"""
        # 文件菜单
        file_menu = self.menuBar().addMenu("📁 文件")

        export_all_action = QAction(QIcon("icons/export.png"), "导出所有密钥", self)
        import_action = QAction(QIcon("icons/import.png"), "导入密钥", self)
        exit_action = QAction(QIcon("icons/exit.png"), "退出", self)

        export_all_action.triggered.connect(self.export_secrets)
        import_action.triggered.connect(self.import_secrets)
        exit_action.triggered.connect(self.close)

        file_menu.addAction(export_all_action)
        file_menu.addAction(import_action)
        file_menu.addSeparator()
        file_menu.addAction(exit_action)

        # 密钥菜单
        secret_menu = self.menuBar().addMenu("🔑 密钥管理")
        add_action = QAction(QIcon("icons/add.png"), "添加密钥", self)
        add_action.triggered.connect(self.add_secret)

        secret_menu.addAction(add_action)

        # 帮助菜单
        help_menu = self.menuBar().addMenu("❓ 帮助")
        about_action = QAction(QIcon("icons/about.png"), "关于", self)
        about_action.triggered.connect(self.show_about_dialog)
        help_menu.addAction(about_action)

    def add_secret(self):
        """添加新密钥"""
        name, ok1 = QInputDialog.getText(
            self, "添加密钥",
            "请输入密钥名称：",
            QLineEdit.Normal,
            "",
            Qt.Dialog | Qt.CustomizeWindowHint | Qt.WindowTitleHint
        )
        if not ok1 or not name.strip():
            return

        secret, ok2 = QInputDialog.getText(
            self, "添加密钥",
            "请输入 Base32 编码的密钥：",
            QLineEdit.Normal,
            "",
            Qt.Dialog | Qt.CustomizeWindowHint | Qt.WindowTitleHint
        )
        if not ok2 or not secret.strip():
            return

        try:
            self.core.add_secret(name.strip(), secret.strip())
            self.refresh_table()
            self.statusBar().showMessage(f"成功添加密钥：{name.strip()}", 3000)
        except ValueError as e:
            QMessageBox.critical(self, "错误", str(e))

    def remove_selected_secret(self):
        """删除选中密钥（可多选删除）"""
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "警告", "请先选择要删除的密钥！")
            return

        # 二次确认
        reply = QMessageBox.question(
            self, "确认删除",
            f"确定要删除选中的 {len(selected_rows)} 条密钥吗？",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return

        # 从后往前删，避免行号变化
        for index in sorted(selected_rows, key=lambda x: x.row(), reverse=True):
            row = index.row()
            key_name = self.table.item(row, 0).text()
            self.core.remove_secret(key_name)

        self.refresh_table()
        self.statusBar().showMessage(f"已删除 {len(selected_rows)} 条密钥", 3000)

    def export_secrets(self):
        """导出所有密钥"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出密钥",
            "", "加密文件 (*.enc)",
            options=QFileDialog.DontUseNativeDialog
        )
        if file_path:
            password, ok = QInputDialog.getText(
                self, "设置密码",
                "请输入导出文件密码：",
                QLineEdit.Password,
                flags=Qt.Dialog | Qt.CustomizeWindowHint | Qt.WindowTitleHint
            )
            if ok and password:
                try:
                    self.core.export_secrets(file_path, password)
                    QMessageBox.information(
                        self, "导出成功",
                        f"密钥已成功导出到：\n{file_path}",
                        QMessageBox.Ok
                    )
                except Exception as e:
                    QMessageBox.critical(
                        self, "导出失败",
                        f"导出过程中发生错误：\n{str(e)}",
                        QMessageBox.Ok
                    )

    def export_selected_secrets(self):
        """
        导出选中密钥（多个）。
        使用 self.core.export_specific_secrets 来处理
        """
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "警告", "请先选择要导出的密钥！")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出选中密钥",
            "", "加密文件 (*.enc)",
            options=QFileDialog.DontUseNativeDialog
        )
        if not file_path:
            return

        password, ok = QInputDialog.getText(
            self, "设置密码",
            "请输入导出文件密码：",
            QLineEdit.Password,
            flags=Qt.Dialog | Qt.CustomizeWindowHint | Qt.WindowTitleHint
        )
        if not ok or not password:
            return

        # 收集选中的 (name, secret)
        secrets_to_export = []
        for index in selected_rows:
            row = index.row()
            name = self.table.item(row, 0).text()
            secret = self.table.item(row, 0).data(Qt.UserRole)  # 存在于第一列的UserRole
            if name and secret:
                secrets_to_export.append((name, secret))

        if not secrets_to_export:
            QMessageBox.warning(self, "警告", "无有效密钥可导出！")
            return

        try:
            self.core.export_specific_secrets(secrets_to_export, file_path, password)
            QMessageBox.information(
                self, "导出成功",
                f"选中的密钥已成功导出到：\n{file_path}",
                QMessageBox.Ok
            )
        except Exception as e:
            QMessageBox.critical(
                self, "导出失败",
                f"导出过程中发生错误：\n{str(e)}",
                QMessageBox.Ok
            )

    def refresh_table(self):
        """刷新表格数据"""
        self.table.setRowCount(0)
        secrets = self.core.get_secrets()

        for name, secret in secrets:
            row = self.table.rowCount()
            self.table.insertRow(row)

            # 密钥名称
            name_item = QTableWidgetItem(name)
            # 用 UserRole 存储真正的 secret 值，方便其他地方直接获取
            name_item.setData(Qt.UserRole, secret)
            self.table.setItem(row, 0, name_item)

            # 验证码和剩余时间
            try:
                token = TOTP.get_totp_token(secret)
                remaining = 30 - int(time.time() % 30)

                # 验证码显示
                token_item = QTableWidgetItem(token)
                token_item.setFont(QFont("Consolas", 14, QFont.Bold))
                self.table.setItem(row, 1, token_item)

                # 剩余时间
                time_item = QTableWidgetItem(f"{remaining} 秒")
                time_item.setFont(QFont("Arial", 11, QFont.Medium))
                self.table.setItem(row, 2, time_item)

            except Exception:
                # 若密钥无效则显示提示
                error_item = QTableWidgetItem("无效密钥")
                self.table.setItem(row, 1, error_item)
                self.table.setItem(row, 2, QTableWidgetItem("N/A"))

            # 操作区：查看/编辑、删除、导出
            btn_widget = QWidget()
            btn_layout = QHBoxLayout(btn_widget)
            btn_layout.setContentsMargins(0, 0, 0, 0)
            btn_layout.setSpacing(6)

            # 查看/编辑
            view_btn = QPushButton("查看/编辑")
            view_btn.setIcon(QIcon("icons/edit.png"))
            view_btn.clicked.connect(lambda _, n=name, s=secret: self.view_edit_secret(n, s))
            btn_layout.addWidget(view_btn)

            # 删除
            remove_btn = QPushButton("删除")
            remove_btn.setIcon(QIcon("icons/remove.png"))
            remove_btn.clicked.connect(lambda _, n=name: self.remove_single_secret(n))
            btn_layout.addWidget(remove_btn)

            # 导出
            export_btn = QPushButton("导出")
            export_btn.setIcon(QIcon("icons/export_part.png"))
            export_btn.clicked.connect(lambda _, n=name, s=secret: self.export_single_secret(n, s))
            btn_layout.addWidget(export_btn)

            btn_layout.addStretch()
            self.table.setCellWidget(row, 3, btn_widget)

        # 更新状态栏
        self.statusBar().showMessage(f"就绪 | 总密钥数: {len(secrets)}")

    def remove_single_secret(self, name):
        """删除单个密钥"""
        reply = QMessageBox.question(
            self, "确认删除",
            f"确定要删除密钥 '{name}' 吗？",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.core.remove_secret(name)
            self.refresh_table()
            self.statusBar().showMessage(f"已删除密钥：{name}", 3000)

    def export_single_secret(self, name, secret):
        """导出单个密钥"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出密钥",
            f"{name}.enc", "加密文件 (*.enc)",
            options=QFileDialog.DontUseNativeDialog
        )
        if not file_path:
            return

        password, ok = QInputDialog.getText(
            self, "设置密码",
            f"为 '{name}' 设定导出文件密码：",
            QLineEdit.Password,
            flags=Qt.Dialog | Qt.CustomizeWindowHint | Qt.WindowTitleHint
        )
        if not ok or not password:
            return

        try:
            # 通过核心逻辑只导出此一条
            self.core.export_specific_secrets([(name, secret)], file_path, password)
            QMessageBox.information(
                self, "导出成功",
                f"密钥 '{name}' 已成功导出到：\n{file_path}",
                QMessageBox.Ok
            )
        except Exception as e:
            QMessageBox.critical(
                self, "导出失败",
                f"导出过程中发生错误：\n{str(e)}",
                QMessageBox.Ok
            )

    def view_edit_secret(self, name, secret):
        """查看/编辑密钥"""

        def save_callback(new_name, new_secret):
            self.core.remove_secret(name)
            self.core.add_secret(new_name, new_secret)
            self.refresh_table()
            self.statusBar().showMessage(f"成功更新密钥：{new_name}", 3000)

        dialog = SecretDetailsDialog(self, name, secret, save_callback)
        dialog.exec_()

    def update_totps(self):
        """更新验证码显示"""
        current_time = time.time()
        if int(current_time % 30) == 0:
            # 每30秒完整刷新一次
            self.refresh_table()
        else:
            # 每秒更新剩余时间
            for row in range(self.table.rowCount()):
                remaining = 30 - int(current_time % 30)
                time_item = self.table.item(row, 2)
                if time_item:
                    time_item.setText(f"{remaining} 秒")

    def show_about_dialog(self):
        """显示关于对话框"""
        about_text = """
        <h3>离线2FA验证工具（安全版）</h3>
        <p>版本：1.0</p>
        <p>作者：Hellohistory</p>
        <p>特性：</p>
        <ul>
            <li>完全离线运行且开源</li>
            <li>加密存储</li>
            <li>支持TOTP标准</li>
            <li>跨平台支持</li>
        </ul>
        <hr>
        <h4>开源信息</h4>
        <p>本项目核心代码采用 <b>MIT</b> 协议开源。</p>由于使用<b>QT</b>制作GUI，所以GUI部分为<b>GPL</b>协议
        <p>查看源代码请访问：
            <a href="https://github.com/Hellohistory/OpenPrepTools" target="_blank">GitHub</a> 
            或 
            <a href="https://gitee.com/Hellohistory/OpenPrepTools" target="_blank">Gitee</a>
        </p>
        """

        msg = QMessageBox(self)
        msg.setWindowTitle("关于")
        msg.setIconPixmap(QPixmap("icon.png").scaled(64, 64))
        msg.setTextFormat(Qt.RichText)  # 允许使用富文本（HTML）
        msg.setText(about_text)
        msg.exec_()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    password, ok = QInputDialog.getText(
        None,
        "密码验证",
        "请输入主密码：\n\n（该密码将用于保护您所有的离线 2FA 密钥，此密码无法恢复，无法找回，请务必牢记！！！！！！）",
        QLineEdit.Password,
        flags=Qt.Dialog | Qt.CustomizeWindowHint | Qt.WindowTitleHint
    )

    if ok and password:
        try:
            window = SecureTOTPManagerGUI(password)
            window.show()
            sys.exit(app.exec_())
        except Exception as e:
            QMessageBox.critical(
                None, "致命错误",
                f"程序初始化失败：\n{str(e)}",
                QMessageBox.Ok
            )
            sys.exit(1)
