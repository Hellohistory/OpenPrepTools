import sys
import pyperclip
from PyQt5.QtCore import QSettings, QTranslator, QLocale, Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (QApplication, QWidget, QLabel, QLineEdit, QCheckBox, QPushButton, QVBoxLayout, QHBoxLayout,
                             QMessageBox, QTextEdit, QGroupBox, QGridLayout, QSplitter)
from zxcvbn import zxcvbn

from password_generation import PasswordGenerator
from password_generator_api import start_fastapi
from password_strength import translate_suggestion

# API 服务器线程和状态变量
server_thread = None
server_running = False
server_port = 25698


class PasswordGeneratorApp(QWidget):
    def __init__(self):
        super().__init__()
        self.settings = QSettings('YourCompany', 'PasswordGeneratorApp')
        self.translator = QTranslator()
        self.initUI()
        self.load_settings()
        self.load_language()

    def initUI(self):
        self.setWindowTitle('一次性密码生成      By Hellohistory')
        self.setWindowIcon(QIcon('logo_5.ico'))

        # 创建标签和输入框
        self.length_label = QLabel('密码长度:')
        self.length_entry = QLineEdit(self)

        # 创建复选框
        self.lowercase_var = QCheckBox('小写字母', self)
        self.uppercase_var = QCheckBox('大写字母', self)
        self.digits_var = QCheckBox('数字', self)
        self.punctuation_var = QCheckBox('标点符号', self)

        # 创建API开关
        self.api_var = QCheckBox('启用API', self)
        self.api_var.setChecked(False)
        self.api_var.stateChanged.connect(self.toggle_api)

        # 创建生成按钮
        self.generate_button = QPushButton('生成密码', self)
        self.generate_button.clicked.connect(self.generate_password)

        # 创建批量生成相关控件
        self.bulk_count_label = QLabel('批量密码生成数量:')
        self.bulk_count_entry = QLineEdit(self)
        self.generate_bulk_button = QPushButton('批量生成', self)
        self.generate_bulk_button.clicked.connect(self.generate_bulk_passwords)

        # 创建密码显示框
        self.password_label = QLabel('生成的密码:')
        self.password_entry = QTextEdit(self)
        self.password_entry.setReadOnly(True)

        # 创建复制按钮
        self.copy_button = QPushButton('复制密码', self)
        self.copy_button.clicked.connect(self.copy_password)

        # 创建批量密码复制按钮
        self.copy_bulk_button = QPushButton('复制批量密码', self)
        self.copy_bulk_button.clicked.connect(self.copy_bulk_passwords)

        # 创建用户输入密码的框
        self.user_password_label = QLabel('输入密码:')
        self.user_password_entry = QTextEdit(self)  # 改为 QTextEdit
        self.check_strength_button = QPushButton('检查密码强度', self)
        self.check_strength_button.clicked.connect(self.check_password_strength)

        # 创建密码强度显示框
        self.password_strength_label = QLabel('密码强度:')
        self.password_feedback_label = QLabel('建议:')

        # 创建黑暗模式开关
        self.dark_mode_var = QCheckBox('黑暗模式', self)
        self.dark_mode_var.stateChanged.connect(self.toggle_dark_mode)

        # 创建批量生成显示框
        self.bulk_passwords_entry = QTextEdit(self)
        self.bulk_passwords_entry.setReadOnly(True)

        # 创建分组框
        self.settings_group_box = QGroupBox("密码生成设置")
        self.api_group_box = QGroupBox("其他设置")
        self.output_group_box = QGroupBox("密码输出")
        self.bulk_group_box = QGroupBox("批量密码生成")
        self.user_password_group_box = QGroupBox("密码强度检测")

        # 布局设置
        self.layout_setup()

    def layout_setup(self):
        main_layout = QVBoxLayout()

        # 设置布局
        settings_layout = QGridLayout()
        settings_layout.addWidget(self.length_label, 0, 0)
        settings_layout.addWidget(self.length_entry, 0, 1)
        settings_layout.addWidget(self.lowercase_var, 1, 0)
        settings_layout.addWidget(self.uppercase_var, 1, 1)
        settings_layout.addWidget(self.digits_var, 2, 0)
        settings_layout.addWidget(self.punctuation_var, 2, 1)
        self.settings_group_box.setLayout(settings_layout)

        # API布局
        api_layout = QHBoxLayout()
        api_layout.addWidget(self.api_var)
        api_layout.addWidget(self.dark_mode_var)
        self.api_group_box.setLayout(api_layout)

        # 输出布局
        output_layout = QVBoxLayout()
        output_layout.addWidget(self.password_label)
        output_layout.addWidget(self.password_entry)
        output_buttons_layout = QHBoxLayout()
        output_buttons_layout.addWidget(self.generate_button)
        output_buttons_layout.addWidget(self.copy_button)
        output_layout.addLayout(output_buttons_layout)
        self.output_group_box.setLayout(output_layout)

        # 批量生成布局
        bulk_layout = QVBoxLayout()
        bulk_count_layout = QHBoxLayout()
        bulk_count_layout.addWidget(self.bulk_count_label)
        bulk_count_layout.addWidget(self.bulk_count_entry)
        bulk_count_layout.addWidget(self.generate_bulk_button)
        bulk_layout.addLayout(bulk_count_layout)
        bulk_layout.addWidget(self.bulk_passwords_entry)
        bulk_layout.addWidget(self.copy_bulk_button)
        self.bulk_group_box.setLayout(bulk_layout)

        # 用户密码检测布局
        user_password_layout = QVBoxLayout()
        user_password_layout.addWidget(self.user_password_label)
        user_password_layout.addWidget(self.user_password_entry)
        user_password_layout.addWidget(self.check_strength_button)
        user_password_layout.addWidget(self.password_strength_label)
        user_password_layout.addWidget(self.password_feedback_label)
        self.user_password_group_box.setLayout(user_password_layout)

        # 创建分隔器
        splitter = QSplitter(Qt.Horizontal)
        left_widget = QWidget()
        right_widget = QWidget()
        left_layout = QVBoxLayout()
        right_layout = QVBoxLayout()
        left_layout.addWidget(self.settings_group_box)
        left_layout.addWidget(self.api_group_box)
        left_layout.addWidget(self.user_password_group_box)
        right_layout.addWidget(self.output_group_box)
        right_layout.addWidget(self.bulk_group_box)
        left_widget.setLayout(left_layout)
        right_widget.setLayout(right_layout)
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)

        main_layout.addWidget(splitter)

        self.setLayout(main_layout)

    def toggle_api(self):
        global server_thread, server_running, server_port
        if self.api_var.isChecked():
            if server_running:
                QMessageBox.information(self, "API 启动", f"API 已在端口 {server_port} 运行")
            else:
                while True:
                    try:
                        server_thread = start_fastapi(server_port)
                        server_thread.start()
                        server_running = True
                        print(f"API started on port {server_port}")
                        QMessageBox.information(self, "API 启动", f"API 已在端口 {server_port} 启动")
                        break
                    except Exception as e:
                        if "error while attempting to bind on address" in str(e):
                            server_port += 1
                            print(f"Port {server_port - 1} is in use, trying port {server_port}")
                        else:
                            raise e
        else:
            if server_thread and server_thread.is_alive():
                server_thread.stop()
                server_thread.join()
                server_running = False
                QMessageBox.information(self, "API 停止", "API 已关闭")

    def generate_password(self):
        try:
            base_length = int(self.length_entry.text())
            char_types = []
            if self.lowercase_var.isChecked():
                char_types.append('lowercase')
            if self.uppercase_var.isChecked():
                char_types.append('uppercase')
            if self.digits_var.isChecked():
                char_types.append('digits')
            if self.punctuation_var.isChecked():
                char_types.append('punctuation')

            generator = PasswordGenerator(base_length=base_length, char_types=char_types)

            password = generator.password_generator()
            self.password_entry.setText(password)
            self.display_password_strength(password)
        except Exception as e:
            QMessageBox.critical(self, "错误", str(e))

    def display_password_strength(self, password):
        strength = zxcvbn(password)
        score = strength['score']
        feedback = strength['feedback']['suggestions']
        # 将建议翻译成中文
        feedback_cn = [translate_suggestion(s) for s in feedback]
        # 显示评分和反馈
        self.password_strength_label.setText(f"密码强度: {score}/4")
        self.password_feedback_label.setText("建议: " + ", ".join(feedback_cn))

    def check_password_strength(self):
        password = self.user_password_entry.toPlainText()
        self.display_password_strength(password)

    def generate_bulk_passwords(self):
        try:
            count = int(self.bulk_count_entry.text())
            base_length = int(self.length_entry.text())
            char_types = []
            if self.lowercase_var.isChecked():
                char_types.append('lowercase')
            if self.uppercase_var.isChecked():
                char_types.append('uppercase')
            if self.digits_var.isChecked():
                char_types.append('digits')
            if self.punctuation_var.isChecked():
                char_types.append('punctuation')

            generator = PasswordGenerator(base_length=base_length, char_types=char_types)

            passwords = [generator.password_generator() for _ in range(count)]
            self.display_bulk_passwords(passwords)
        except Exception as e:
            QMessageBox.critical(self, "错误", str(e))

    def display_bulk_passwords(self, passwords):
        bulk_passwords = "\n".join(passwords)
        self.bulk_passwords_entry.setText(bulk_passwords)

    def copy_password(self):
        password = self.password_entry.toPlainText()
        pyperclip.copy(password)
        QMessageBox.information(self, "复制成功", "密码已复制到剪贴板")

    def copy_bulk_passwords(self):
        passwords = self.bulk_passwords_entry.toPlainText()
        pyperclip.copy(passwords)
        QMessageBox.information(self, "复制成功", "批量密码已复制到剪贴板")

    def toggle_dark_mode(self):
        if self.dark_mode_var.isChecked():
            self.setStyleSheet("QWidget { background-color: #2e2e2e; color: #ffffff; }")
        else:
            self.setStyleSheet("")

    def save_settings(self):
        self.settings.setValue('length', self.length_entry.text())
        self.settings.setValue('lowercase', self.lowercase_var.isChecked())
        self.settings.setValue('uppercase', self.uppercase_var.isChecked())
        self.settings.setValue('digits', self.digits_var.isChecked())
        self.settings.setValue('punctuation', self.punctuation_var.isChecked())
        self.settings.setValue('dark_mode', self.dark_mode_var.isChecked())

    def load_settings(self):
        self.length_entry.setText(self.settings.value('length', '12'))
        self.lowercase_var.setChecked(self.settings.value('lowercase', True, type=bool))
        self.uppercase_var.setChecked(self.settings.value('uppercase', True, type=bool))
        self.digits_var.setChecked(self.settings.value('digits', True, type=bool))
        self.punctuation_var.setChecked(self.settings.value('punctuation', True, type=bool))
        self.dark_mode_var.setChecked(self.settings.value('dark_mode', False, type=bool))

    def load_language(self):
        locale = QLocale.system().name()
        self.translator.load(f"translation_{locale}.qm")
        QApplication.instance().installTranslator(self.translator)

    def closeEvent(self, event):
        self.save_settings()
        event.accept()


if __name__ == '__main__':
    qt_app = QApplication(sys.argv)
    ex = PasswordGeneratorApp()
    ex.show()
    sys.exit(qt_app.exec_())
