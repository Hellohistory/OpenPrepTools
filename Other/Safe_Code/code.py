import concurrent.futures
import hashlib
import os
import secrets
import string
import sys
import time
import warnings

import pyperclip
from PyQt5.QtCore import QSettings, QTranslator, QLocale, Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (QApplication, QWidget, QLabel, QLineEdit, QCheckBox, QPushButton, QVBoxLayout, QHBoxLayout,
                             QMessageBox, QTextEdit, QGroupBox, QGridLayout, QSplitter)
from zxcvbn import zxcvbn

def translate_suggestion(suggestion):
    translations = {
        "Use a few words, avoid common phrases": "使用几个单词，避免常见短语",
        "No need for symbols, digits, or uppercase letters": "不需要符号、数字或大写字母",
        "Add another word or two. Uncommon words are better.": "再添加一个或两个单词。不常见的词更好。",
        "Straight rows of keys are easy to guess": "直排键很容易被猜到",
        "Short keyboard patterns are easy to guess": "短键盘图案很容易被猜到",
        "Use a longer keyboard pattern with more turns": "使用更长的键盘图案，多转几次",
        "Avoid repeated words and characters": "避免重复的单词和字符",
        "Avoid sequences": "避免顺序",
        "Avoid recent years": "避免使用最近的年份",
        "Avoid years that are associated with you": "避免使用与你相关的年份",
        "Avoid dates and years that are associated with you": "避免使用与你相关的日期和年份",
        "Avoid repeated words and chaacters": "避免重复的单词和字符",
        "Capitalization doesn't help very much": "大写帮助不大",
        "All-uppercase is almost as easy to guess as all-lowercase": "全大写几乎和全小写一样容易猜到",
        "Reversed words aren't much harder to guess": "反转单词并没有难多少",
        "Predictable substitutions like '@' instead of 'a' don't help very much": "可预测的替换（如 '@' 代替 'a'）帮助不大"
    }
    return translations.get(suggestion, suggestion)




from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import threading
import uvicorn

fastapi_app = FastAPI()


class PasswordRequest(BaseModel):
    length: int
    lowercase: bool
    uppercase: bool
    digits: bool
    punctuation: bool


@fastapi_app.post("/generate-password/")
def generate_password(request: PasswordRequest):
    try:
        char_types = []
        if request.lowercase:
            char_types.append('lowercase')
        if request.uppercase:
            char_types.append('uppercase')
        if request.digits:
            char_types.append('digits')
        if request.punctuation:
            char_types.append('punctuation')

        generator = PasswordGenerator(base_length=request.length, char_types=char_types)
        password = generator.password_generator()
        return {"password": password}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class ServerThread(threading.Thread):
    def __init__(self, port):
        threading.Thread.__init__(self)
        self.port = port
        self.server = None

    def run(self):
        config = uvicorn.Config(fastapi_app, host="0.0.0.0", port=self.port)
        self.server = uvicorn.Server(config)
        self.server.run()

    def stop(self):
        if self.server:
            self.server.should_exit = True


def start_fastapi(port=25698):
    server_thread = ServerThread(port)
    return server_thread


def stop_fastapi(server_thread):
    if server_thread and server_thread.is_alive():
        server_thread.stop()
        server_thread.join()



def _create_mixed_hash(hash_value):
    hash_sha256 = hashlib.sha256(hash_value.encode('utf-8')).hexdigest()
    hash_md5 = hashlib.md5(hash_value.encode('utf-8')).hexdigest()
    reversed_hash = (hash_sha256 + hash_md5)[::-1]
    return hashlib.sha256(reversed_hash.encode('utf-8')).hexdigest() + hashlib.md5(
        reversed_hash.encode('utf-8')).hexdigest()


def _concatenate_and_swap(mixed_hash_value):
    concatenate_times = secrets.randbelow(5) + 1  # [1, 5]
    for _ in range(concatenate_times):
        mixed_hash_value += hashlib.sha256(mixed_hash_value.encode('utf-8')).hexdigest()

    mixed_hash_list = list(mixed_hash_value)
    swap_times = secrets.randbelow(10) + 1  # [1, 10]
    for _ in range(swap_times):
        idx1, idx2 = secrets.SystemRandom().sample(range(len(mixed_hash_list)), 2)
        mixed_hash_list[idx1], mixed_hash_list[idx2] = mixed_hash_list[idx2], mixed_hash_list[idx1]

    return ''.join(mixed_hash_list)


class PasswordGenerator:
    CHAR_SET_MAP = {
        'lowercase': (string.ascii_lowercase, 1),  # 小写字母
        'uppercase': (string.ascii_uppercase, 1),  # 大写字母
        'digits': (string.digits, 1),  # 数字
        'punctuation': (string.punctuation, 1)  # 标点符号
    }

    def __init__(self, base_length=10, char_types=None):
        if char_types is None:
            char_types = ['lowercase', 'uppercase', 'digits', 'punctuation']
        self.base_length = base_length
        self.char_sets = self._initialize_char_sets(char_types)

    def _initialize_char_sets(self, char_types):
        """
        初始化字符集。
        :param char_types: 一个包含字符类型的列表，例如 ['lowercase', 'digits']
        :return: 根据指定类型组合的字符集列表
        """
        return [self.CHAR_SET_MAP[char_type] for char_type in char_types if char_type in self.CHAR_SET_MAP]

    def generate_password(self, hash_value):
        mixed_hash_value = _create_mixed_hash(hash_value)
        _concatenate_and_swap(mixed_hash_value)
        return self._create_password()

    def _create_password(self):
        # 确保密码长度严格按照用户指定的 base_length
        password_length = self.base_length
        password_chars = []

        # 根据密码类型，从对应的字符集中选择字符
        for i in range(password_length):
            weights = [weight for _, weight in self.char_sets]
            char_set, _ = secrets.SystemRandom().choices(self.char_sets, weights=weights, k=1)[0]
            password_chars.append(secrets.choice(char_set))
        return ''.join(password_chars)

    def password_generator(self):
        enhancer = RandomDataEnhancer()
        random_hash = enhancer.main()
        password = self.generate_password(random_hash)
        return password

class RandomDataEnhancer:
    def __init__(self):
        self.system_random = secrets.SystemRandom()
        self.logistic_r = self.system_random.uniform(3.57, 4.0)  # Logistic映射的参数选择在混沌区间

    def logistic_map(self, x):
        """Logistic映射，用于生成混沌序列。"""
        return self.logistic_r * x * (1 - x)

    def generate_chaotic_sequence(self, count=100):
        """生成一个混沌序列作为随机数源。使用系统随机数生成器确定初始值。"""
        x = self.system_random.random()  # 使用系统随机数生成器确定初始值
        return [self.logistic_map(x := self.logistic_map(x)) for _ in range(count)]

    def generate_random_floats(self, count=7000, start=1, end=10000000):
        """
        生成指定数量的随机浮点数列表。
        """
        return [self.system_random.uniform(start, end) for _ in range(count)]

    def generate_random_ints(self, count=8000, start=10000, end=6000000000):
        """
        生成指定数量的随机整数列表。
        """
        return [self.system_random.randint(start, end) for _ in range(count)]

    def shuffle_and_select(self, nums, sample_size=15000):
        """
        将数字列表随机打乱，并选择指定数量的样本。
        """
        self.system_random.shuffle(nums)
        return self.system_random.sample(nums, min(len(nums), sample_size))

    def append_system_info(self, nums):
        """
        添加系统时间和操作系统类型到数字列表中。
        """
        return nums + [time.time(), hash(os.name), os.getpid(), self.system_random.randrange(1000000)]

    def enhance_randomness(self, data_str, enable_extra=True):
        """
        对数据字符串进行复杂的随机性增强，此处添加混沌序列。
        """
        if not enable_extra:
            return data_str

        # 添加混沌序列
        chaotic_sequence = ''.join(map(str, self.generate_chaotic_sequence()))
        data_str += chaotic_sequence

        # 剩余增强操作
        operations = ['reverse', 'shuffle', 'insert', 'delete']
        for _ in range(secrets.randbelow(10) + 1):  # [1, 10]
            operation = self.system_random.choice(operations)
            if operation == 'reverse':
                data_str = data_str[::-1]
            elif operation == 'shuffle':
                data_str = ''.join(self.system_random.sample(data_str, len(data_str)))
            elif operation == 'insert':
                insert_pos = self.system_random.randint(0, len(data_str))
                data_str = data_str[:insert_pos] + secrets.token_hex(1) + data_str[insert_pos:]
            elif operation == 'delete' and len(data_str) > 1:
                delete_pos = self.system_random.randint(0, len(data_str) - 1)
                data_str = data_str[:delete_pos] + data_str[delete_pos + 1:]

        return data_str

    def generate_final_hash(self, data):
        """
        生成最终的哈希值。
        """
        hash_func = self.system_random.choice([hashlib.sha256, hashlib.sha512, hashlib.sha3_256, hashlib.sha3_512])
        return hash_func(data.encode()).hexdigest()

    def main(self):
        with concurrent.futures.ThreadPoolExecutor() as executor:
            floats_future = executor.submit(self.generate_random_floats)
            ints_future = executor.submit(self.generate_random_ints)

            floats = floats_future.result()
            ints = ints_future.result()

        all_nums = floats + ints

        selected_nums = self.shuffle_and_select(all_nums)
        selected_with_info = self.append_system_info(selected_nums)
        num_str = convert_to_string(selected_with_info)

        hashes = generate_hashes(num_str)
        concatenated_hashes = ''.join(hashes)

        salted_hashed = salt_and_hash(concatenated_hashes)
        final_hash_with_randomness = self.enhance_randomness(salted_hashed, enable_extra=True)

        final_hash = self.generate_final_hash(final_hash_with_randomness)

        return final_hash


def incorporate_process_info(data_str):
    """融合程序进程信息到数据字符串。"""
    process_info = f"{time.time()}{os.getpid()}{os.getloadavg()[0]}"
    return data_str + process_info


def generate_hashes(data_str):
    """
    生成多种哈希值。
    """
    hash_types = [hashlib.md5, hashlib.sha1, hashlib.sha256, hashlib.blake2b, hashlib.blake2s, hashlib.sha3_256,
                  hashlib.sha3_512]
    return [hash_func(data_str.encode()).hexdigest() for hash_func in hash_types]


def convert_to_string(nums):
    """
    将数字列表转换为字符串。
    """
    return ''.join(map(str, nums))


def salt_and_hash(concatenated_hashes):
    """
    对哈希结果添加随机盐，并进行进一步的哈希计算。
    """
    salt = secrets.token_bytes(16).hex()
    salted_data = concatenated_hashes + salt
    final_hash_types = [hashlib.sha256, hashlib.sha512, hashlib.sha3_256, hashlib.sha3_512]
    return ''.join([hash_func(salted_data.encode()).hexdigest() for hash_func in final_hash_types])

warnings.filterwarnings("ignore", category=DeprecationWarning)

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
        self.setWindowIcon(QIcon('logo.ico'))

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

        # 创建项目链接标签
        self.github_link = QLabel('<a href="https://github.com/Hellohistory/OpenPrepTools">GitHub</a>')
        self.github_link.setOpenExternalLinks(True)
        self.gitee_link = QLabel('<a href="https://gitee.com/Hellohistory/OpenPrepTools">Gitee</a>')
        self.gitee_link.setOpenExternalLinks(True)

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

        # 添加项目链接标签
        project_links_layout = QHBoxLayout()
        project_links_layout.addWidget(self.github_link)
        project_links_layout.addWidget(self.gitee_link)
        main_layout.addLayout(project_links_layout)

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
