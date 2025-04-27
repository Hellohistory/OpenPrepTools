# 2fa_tool_gui.py
import sys
import time
from functools import partial

from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QIcon, QFont, QPixmap
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
    QComboBox,
    QSpinBox,
)

from secure_manager_core import (
    SecureTOTPManager,
    export_specific_secrets,
)
from totp_hotp_core import TOTP, HOTP


class SecretDetailsDialog(QDialog):
    """密钥详情及编辑对话框，支持 TOTP/HOTP"""

    def __init__(self, parent, name, secret, algo, counter, save_callback):
        super().__init__(parent)
        self.save_callback = save_callback
        self.setWindowTitle("🔑 查看/编辑密钥详情")
        self.setWindowIcon(QIcon("icon.png"))
        self.resize(500, 260)

        # ------ 表单布局（实例属性，供外部方法访问） ------
        self.form_layout = QFormLayout()
        self.form_layout.setContentsMargins(24, 24, 24, 24)
        self.form_layout.setVerticalSpacing(12)
        self.form_layout.setHorizontalSpacing(20)

        # 名称
        self.name_input = QLineEdit(name)
        self.form_layout.addRow(QLabel("密钥名称："), self.name_input)

        # Base32 密钥
        self.secret_input = QLineEdit(secret)
        self.secret_input.setFont(QFont("Consolas", 12))
        self.form_layout.addRow(QLabel("Base32 密钥："), self.secret_input)

        # 算法模式
        self.algo_input = QComboBox()
        self.algo_input.addItems(["TOTP", "HOTP"])
        self.algo_input.setCurrentText(algo)
        self.form_layout.addRow(QLabel("算法模式："), self.algo_input)

        # HOTP 计数器
        self.counter_input = QSpinBox()
        self.counter_input.setRange(0, 2_147_483_647)
        self.counter_input.setValue(counter)
        self.form_layout.addRow(QLabel("HOTP 计数值："), self.counter_input)

        # 按钮区
        btn_layout = QHBoxLayout()
        self.save_btn = QPushButton("💾 保存")
        self.save_btn.clicked.connect(self.save_changes)  # <-- 这里会找方法
        self.cancel_btn = QPushButton("❌ 取消")
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addStretch()
        btn_layout.addWidget(self.save_btn)
        btn_layout.addWidget(self.cancel_btn)
        self.form_layout.addRow(btn_layout)

        self.setLayout(self.form_layout)

        # ⚠️ 信号放最后再连，属性已经就位
        self.algo_input.currentTextChanged.connect(self._on_algo_changed)
        self._on_algo_changed(algo)

    # ---------- 下面两个方法务必与 __init__ 平级 ----------
    def _on_algo_changed(self, algo_text: str) -> None:
        """根据算法显示/隐藏 HOTP 计数器"""
        is_hotp = (algo_text == "HOTP")
        self.counter_input.setVisible(is_hotp)
        label = self.form_layout.labelForField(self.counter_input)
        if label:
            label.setVisible(is_hotp)

    def save_changes(self) -> None:
        """保存修改，将数据通过回调返回"""
        name = self.name_input.text().strip()
        secret = self.secret_input.text().strip()
        algo = self.algo_input.currentText()
        counter = self.counter_input.value() if algo == "HOTP" else 0

        if not name or not secret:
            QMessageBox.warning(self, "错误", "密钥名称和密钥值不能为空！")
            return

        try:
            self.save_callback(name, secret, algo, counter)
            self.accept()
        except ValueError as exc:
            QMessageBox.warning(self, "错误", str(exc))


class SecureTOTPManagerGUI(QMainWindow):
    """主界面：支持 TOTP 与 HOTP 的离线 2FA 验证工具"""

    def __init__(self, password):
        super().__init__()
        self.setWindowTitle("离线2FA验证工具（安全版）")
        self.setWindowIcon(QIcon("icon.png"))
        self.setGeometry(300, 300, 900, 560)
        self.setMinimumSize(800, 480)

        self.core = SecureTOTPManager(password)
        self.init_ui()
        self.init_menu()
        self.refresh_table()
        self.statusBar().showMessage(
            f"就绪 | 总密钥数: {len(self.core.get_secrets())}"
        )

    def init_ui(self):
        """初始化表格 UI 与定时器"""
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels([
            "🔖 名称", "⚙️ 模式", "🔄 验证码", "⏳ 剩余/计数", "操作"
        ])
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.MultiSelection)
        self.table.setSortingEnabled(True)
        self.table.setFocusPolicy(Qt.NoFocus)

        # 列宽设置
        self.table.setColumnWidth(0, 200)
        self.table.setColumnWidth(1, 80)
        self.table.setColumnWidth(2, 160)
        self.table.setColumnWidth(3, 160)
        self.table.horizontalHeader().setSectionResizeMode(
            4, QHeaderView.Stretch
        )

        self.table.cellDoubleClicked.connect(self.on_cell_double_clicked)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.addWidget(self.table)
        self.setCentralWidget(container)

        # 每秒刷新一次
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_totps)
        self.timer.start(1000)

    def init_menu(self):
        """初始化菜单栏"""
        file_menu = self.menuBar().addMenu("📁 文件")
        exp_all = file_menu.addAction(
            QIcon("icons/export.png"), "导出所有密钥"
        )
        imp = file_menu.addAction(
            QIcon("icons/import.png"), "导入密钥"
        )
        file_menu.addSeparator()
        exit_act = file_menu.addAction(
            QIcon("icons/exit.png"), "退出"
        )
        exp_all.triggered.connect(self.export_secrets)
        imp.triggered.connect(self.import_secrets)
        exit_act.triggered.connect(self.close)

        key_menu = self.menuBar().addMenu("🔑 密钥管理")
        add_key = key_menu.addAction(
            QIcon("icons/add.png"), "添加密钥"
        )
        key_menu.addAction("删除选中", self.remove_selected_secret)
        add_key.triggered.connect(self.add_secret)

        help_menu = self.menuBar().addMenu("❓ 帮助")
        help_menu.addAction(
            QIcon("icons/about.png"), "关于", self.show_about_dialog
        )

    def on_cell_double_clicked(self, row, column):
        """双击验证码列复制到剪贴板"""
        if column == 2:
            item = self.table.item(row, 2)
            if item and item.text():
                QApplication.clipboard().setText(item.text())
                QMessageBox.information(
                    self, "提示", "验证码已复制到剪贴板！"
                )

    def import_secrets(self):
        """导入加密文件"""
        path, _ = QFileDialog.getOpenFileName(
            self, "导入密钥", "", "加密文件 (*.enc)"
        )
        if not path:
            return
        pwd, ok = QInputDialog.getText(
            self, "输入密码", "请输入导出时设置的密码：",
            QLineEdit.Password
        )
        if ok and pwd:
            try:
                self.core.import_secrets(path, pwd)
                self.refresh_table()
                QMessageBox.information(self, "导入成功", "密钥已成功导入！")
            except Exception as e:
                QMessageBox.critical(self, "导入失败", str(e))

    def add_secret(self):
        """添加新密钥，支持选择 TOTP/HOTP"""
        name, ok1 = QInputDialog.getText(
            self, "添加密钥", "请输入密钥名称：", QLineEdit.Normal
        )
        if not ok1 or not name.strip():
            return
        secret, ok2 = QInputDialog.getText(
            self, "添加密钥", "请输入 Base32 编码的密钥：",
            QLineEdit.Normal
        )
        if not ok2 or not secret.strip():
            return
        # 选择算法模式
        algo, ok3 = QInputDialog.getItem(
            self, "选择算法", "请选择验证类型：",
            ["TOTP", "HOTP"], 0, False
        )
        if not ok3:
            return
        counter = 0
        if algo == "HOTP":
            counter, ok4 = QInputDialog.getInt(
                self, "初始计数器", "请输入初始计数值：", 0, 0
            )
            if not ok4:
                return
        try:
            # 增加第四、五参数
            self.core.add_secret(name.strip(), secret.strip(), algo, counter)
            self.refresh_table()
            self.statusBar().showMessage(
                f"成功添加 {algo} 密钥：{name.strip()}", 3000
            )
        except ValueError as e:
            QMessageBox.critical(self, "错误", str(e))

    def remove_selected_secret(self):
        """删除选中的多条密钥"""
        rows = self.table.selectionModel().selectedRows()
        if not rows:
            QMessageBox.warning(self, "警告", "请先选择要删除的密钥！")
            return
        if QMessageBox.question(
            self, "确认删除",
            f"确定要删除 {len(rows)} 条密钥吗？",
            QMessageBox.Yes | QMessageBox.No
        ) != QMessageBox.Yes:
            return
        for idx in sorted(rows, key=lambda x: x.row(), reverse=True):
            name = self.table.item(idx.row(), 0).text()
            self.core.remove_secret(name)
        self.refresh_table()
        self.statusBar().showMessage(
            f"已删除 {len(rows)} 条密钥", 3000
        )

    def export_secrets(self):
        """导出所有密钥到加密文件"""
        path, _ = QFileDialog.getSaveFileName(
            self, "导出密钥", "", "加密文件 (*.enc)"
        )
        if not path:
            return
        pwd, ok = QInputDialog.getText(
            self, "设置密码", "请输入导出文件密码：",
            QLineEdit.Password
        )
        if ok and pwd:
            try:
                self.core.export_secrets(path, pwd)
                QMessageBox.information(
                    self, "导出成功", f"密钥已导出到：\n{path}"
                )
            except Exception as e:
                QMessageBox.critical(self, "导出失败", str(e))

    def refresh_table(self):
        """刷新表格：读出所有密钥并展示模式、验证码、剩余时间/计数"""
        self.table.setSortingEnabled(False)
        self.table.setRowCount(0)

        # 假设 core.get_secrets 返回 (name, secret, algo, counter)
        for name, secret, algo, counter in self.core.get_secrets():
            row = self.table.rowCount()
            self.table.insertRow(row)

            # 名称列，保存元数据
            name_item = QTableWidgetItem(name)
            name_item.setTextAlignment(Qt.AlignCenter)
            name_item.setData(Qt.UserRole, (secret, algo, counter))
            self.table.setItem(row, 0, name_item)

            # 模式列
            mode_item = QTableWidgetItem(algo)
            mode_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 1, mode_item)

            # 验证码与剩余/计数占位
            self.table.setItem(row, 2, QTableWidgetItem())
            self.table.setItem(row, 3, QTableWidgetItem())

            # 操作按钮列
            btn_widget = QWidget()
            btn_layout = QHBoxLayout(btn_widget)
            btn_layout.setContentsMargins(0, 0, 0, 0)
            btn_layout.setSpacing(6)

            # 编辑
            edit_btn = QPushButton("查看/编辑")
            edit_btn.setIcon(QIcon("icons/edit.png"))
            edit_btn.clicked.connect(
                partial(self.view_edit_secret, name, secret, algo, counter)
            )
            btn_layout.addWidget(edit_btn)

            # 删除
            del_btn = QPushButton("删除")
            del_btn.setIcon(QIcon("icons/remove.png"))
            del_btn.clicked.connect(
                partial(self.remove_single_secret, name)
            )
            btn_layout.addWidget(del_btn)

            # 导出单条
            exp_btn = QPushButton("导出")
            exp_btn.setIcon(QIcon("icons/export_part.png"))
            exp_btn.clicked.connect(
                partial(self.export_single_secret, name, secret)
            )
            btn_layout.addWidget(exp_btn)

            # HOTP 专用“下一个”按钮
            if algo == "HOTP":
                next_btn = QPushButton("下一个")
                next_btn.clicked.connect(
                    partial(self.hotp_next, name)
                )
                btn_layout.addWidget(next_btn)

            btn_layout.addStretch()
            self.table.setCellWidget(row, 4, btn_widget)

        self.table.setSortingEnabled(True)
        self.update_totps()
        self.statusBar().showMessage(
            f"就绪 | 总密钥数: {len(self.core.get_secrets())}"
        )

    def update_totps(self):
        """定时更新 TOTP 剩余秒数和 HOTP 计数值"""
        now = time.time()
        remain = 30 - int(now % 30)
        for row in range(self.table.rowCount()):
            secret, algo, counter = self.table.item(
                row, 0
            ).data(Qt.UserRole)

            # 根据算法生成验证码
            try:
                if algo == "TOTP":
                    token = TOTP.get_totp_token(secret)
                    info = f"{remain} 秒"
                else:
                    token = HOTP.generate_hotp(secret, counter)
                    info = f"计数: {counter}"
            except Exception:
                token = "无效密钥"
                info = "-"

            # 写入表格
            self.table.item(row, 2).setText(token)
            self.table.item(row, 3).setText(info)

    def hotp_next(self, name: str):
        """HOTP: 计数器自增并刷新"""
        self.core.increment_counter(name)
        self.refresh_table()

    def remove_single_secret(self, name: str):
        """删除单条密钥"""
        if QMessageBox.question(
            self, "确认删除",
            f"确定要删除密钥 '{name}' 吗？",
            QMessageBox.Yes | QMessageBox.No
        ) == QMessageBox.Yes:
            self.core.remove_secret(name)
            self.refresh_table()
            self.statusBar().showMessage(
                f"已删除密钥：{name}", 3000
            )

    def export_single_secret(self, name: str, secret: str):
        """导出单条密钥"""
        path, _ = QFileDialog.getSaveFileName(
            self, "导出密钥", f"{name}.enc", "加密文件 (*.enc)"
        )
        if not path:
            return
        pwd, ok = QInputDialog.getText(
            self, "设置密码", f"为 '{name}' 设置密码：",
            QLineEdit.Password
        )
        if ok and pwd:
            try:
                export_specific_secrets([(name, secret)], path, pwd)
                QMessageBox.information(
                    self, "导出成功",
                    f"'{name}' 已导出到：\n{path}"
                )
            except Exception as e:
                QMessageBox.critical(self, "导出失败", str(e))

    def view_edit_secret(
        self, name: str, secret: str, algo: str, counter: int
    ):  # noqa: C901
        """查看/编辑单条密钥详情"""
        def save_cb(new_name, new_secret, new_algo, new_counter):
            # 先删除再添加以保持唯一性
            self.core.remove_secret(name)
            self.core.add_secret(
                new_name, new_secret, new_algo, new_counter
            )
            self.refresh_table()
            self.statusBar().showMessage(
                f"成功更新 {new_algo} 密钥：{new_name}", 3000
            )

        dlg = SecretDetailsDialog(
            self, name, secret, algo, counter, save_cb
        )
        dlg.exec()

    def show_about_dialog(self):
        """显示关于对话框"""
        about_html = (
            '<h3>离线2FA验证工具（安全版）</h3>'
            '<p>版本：1.2</p>'
            '<p>作者：Hellohistory</p>'
            '<ul>'
            '<li>完全离线运行且开源</li>'
            '<li>加密存储</li>'
            '<li>支持 TOTP/HOTP</li>'
            '<li>跨平台支持</li>'
            '</ul>'
            '<hr>'
            '<p>协议：核心 MIT 开源，GUI 部分 LGPL 协议</p>'
            '<p>源码：<a href="https://github.com/Hellohistory/'
            'OpenPrepTools">GitHub</a> 或 '
            '<a href="https://gitee.com/Hellohistory/'
            'OpenPrepTools">Gitee</a></p>'
        )
        msg = QMessageBox(self)
        msg.setWindowTitle("关于")
        msg.setIconPixmap(
            QPixmap("icon.png").scaled(64, 64)
        )
        msg.setTextFormat(Qt.RichText)
        msg.setText(about_html)
        msg.exec()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    pwd, ok = QInputDialog.getText(
        None,
        "密码验证",
        "请输入主密码：\n（该密码用于保护所有离线 2FA 密钥，无法找回，请务必牢记）",
        QLineEdit.Password,
    )
    if ok and pwd:
        try:
            window = SecureTOTPManagerGUI(pwd)
            window.show()
            sys.exit(app.exec())
        except Exception as e:
            QMessageBox.critical(None, "致命错误", str(e))
            sys.exit(1)