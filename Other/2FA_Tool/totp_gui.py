import json
import time

from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QPushButton, QTableWidget, QTableWidgetItem, QWidget, QHBoxLayout,
    QMessageBox, QFileDialog, QInputDialog, QHeaderView, QAction
)

from totp_core import TOTP


def create_button(text, slot):
    """创建按钮并绑定槽函数"""
    button = QPushButton(text)
    button.clicked.connect(slot)
    return button


class TOTPManager(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("离线2FA验证工具")
        self.setGeometry(300, 300, 500, 500)
        self.setWindowIcon(QIcon("icon.png"))

        layout = QVBoxLayout()

        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["密钥名称", "当前验证码", "剩余可用时间"])
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table)

        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setColumnWidth(0, 3)
        self.table.setColumnWidth(1, 2)
        self.table.setColumnWidth(2, 1)

        control_layout = QHBoxLayout()

        self.add_button = create_button("添加密钥", self.add_secret)
        self.load_button = create_button("加载密钥文件", self.load_secrets)
        self.save_button = create_button("保存密钥文件", self.save_secrets)
        self.remove_button = create_button("删除选中密钥", self.remove_selected_secret)
        self.export_button = create_button("导出选中密钥", self.export_selected_secret)

        for button in [self.add_button, self.load_button, self.save_button, self.remove_button, self.export_button]:
            control_layout.addWidget(button)

        layout.addLayout(control_layout)

        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_totps)
        self.timer.start(1000)

        self.secrets = {}

        # 创建菜单栏
        self.menu_bar = self.menuBar()
        self.help_menu = self.menu_bar.addMenu("帮助")
        about_action = QAction("关于", self)
        about_action.triggered.connect(self.show_about)
        self.help_menu.addAction(about_action)

    def show_about(self):
        """显示关于窗口"""
        msg = QMessageBox(self)
        msg.setWindowTitle("关于")
        msg.setText(
            "Hellohistory 出品<br>"
            "开源地址：<br>"
            "<a href='https://github.com/Hellohistory/OpenPrepTools'>GitHub 地址</a><br>"
            "<a href='https://gitee.com/Hellohistory/OpenPrepTools'>Gitee 地址</a>"
        )
        msg.setTextFormat(Qt.RichText)  # 启用富文本格式
        msg.setTextInteractionFlags(Qt.TextBrowserInteraction)  # 启用超链接点击功能
        msg.exec_()

    def add_secret(self):
        """添加新的密钥"""
        name, ok1 = QInputDialog.getText(self, "添加密钥", "请输入密钥名称：")
        if not ok1 or not name.strip():
            return

        secret, ok2 = QInputDialog.getText(self, "添加密钥", "请输入 Base32 编码的密钥：")
        if not ok2 or not secret.strip():
            return

        try:
            TOTP.validate_secret(secret)
            if name.strip() in self.secrets:
                QMessageBox.warning(self, "错误", "密钥名称已存在！")
                return
            self.secrets[name.strip()] = secret.strip()
            self.refresh_table()
        except ValueError as e:
            QMessageBox.warning(self, "错误", str(e))

    def load_secrets(self):
        """从文件加载密钥"""
        file_path, _ = QFileDialog.getOpenFileName(self, "选择密钥文件", "", "JSON 文件 (*.json);;所有文件 (*.*)")
        if file_path:
            try:
                with open(file_path, "r") as file:
                    self.secrets = json.load(file)
                    self.refresh_table()
                    QMessageBox.information(self, "加载成功", "密钥已成功加载！")
            except Exception as e:
                QMessageBox.warning(self, "加载失败", f"无法加载密钥：{str(e)}")

    def save_secrets(self):
        """保存密钥到文件"""
        file_path, _ = QFileDialog.getSaveFileName(self, "保存密钥文件", "", "JSON 文件 (*.json);;所有文件 (*.*)")
        if file_path:
            try:
                with open(file_path, "w") as file:
                    json.dump(self.secrets, file)
                    QMessageBox.information(self, "保存成功", "密钥已成功保存！")
            except Exception as e:
                QMessageBox.warning(self, "保存失败", f"无法保存密钥：{str(e)}")

    def export_selected_secret(self):
        """导出选中的密钥到文件"""
        current_row = self.table.currentRow()
        if current_row == -1:
            QMessageBox.warning(self, "错误", "请先选择要导出的密钥！")
            return

        key_name = self.table.item(current_row, 0).text()
        file_path, _ = QFileDialog.getSaveFileName(self, "导出密钥", "", "JSON 文件 (*.json);;所有文件 (*.*)")
        if file_path:
            try:
                with open(file_path, "w") as file:
                    json.dump({key_name: self.secrets[key_name]}, file)
                    QMessageBox.information(self, "导出成功", f"密钥 {key_name} 已成功导出！")
            except Exception as e:
                QMessageBox.warning(self, "导出失败", f"无法导出密钥：{str(e)}")

    def remove_selected_secret(self):
        """删除选中的密钥"""
        current_row = self.table.currentRow()
        if current_row == -1:
            QMessageBox.warning(self, "错误", "请先选择要删除的密钥！")
            return

        key_name = self.table.item(current_row, 0).text()
        del self.secrets[key_name]
        self.refresh_table()

    def refresh_table(self):
        """刷新密钥表格"""
        self.table.setRowCount(0)
        for name, secret in self.secrets.items():
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(name))
            self.update_table_row(row, name, secret)

    def update_table_row(self, row, name, secret):
        """更新表格行的验证码和剩余时间"""
        try:
            token = TOTP.get_totp_token(secret)
            remaining_time = 30 - int(time.time() % 30)
            self.table.setItem(row, 1, QTableWidgetItem(token))
            self.table.setItem(row, 2, QTableWidgetItem(f"{remaining_time} 秒"))
        except ValueError:
            self.table.setItem(row, 1, QTableWidgetItem("无效密钥"))
            self.table.setItem(row, 2, QTableWidgetItem("N/A"))

    def update_totps(self):
        """每秒更新验证码和剩余时间"""
        for row in range(self.table.rowCount()):
            name = self.table.item(row, 0).text()
            secret = self.secrets.get(name)
            self.update_table_row(row, name, secret)


if __name__ == "__main__":
    app = QApplication([])

    app.setStyle("Fusion")

    window = TOTPManager()
    window.show()
    app.exec_()
