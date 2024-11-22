import os
import sys
import re
import requests
from PyQt5 import QtWidgets, QtGui, QtCore
from netease_music_core import url_v1, name_v1, lyric_v1, save_cookie, load_cookie


def sanitize_filename(filename):
    # 去掉 Windows 不允许的特殊字符
    return re.sub(r'[\\/:*?"<>|]', '', filename)


def download_song(song_url, song_name):
    try:
        if not os.path.exists("download"):
            os.makedirs("download")

        sanitized_song_name = sanitize_filename(song_name)
        response = requests.get(song_url, stream=True)
        response.raise_for_status()
        with open(os.path.join("download", f"{sanitized_song_name}.flac"), "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        QtWidgets.QMessageBox.information(None, "成功", f"歌曲已成功下载：download/{sanitized_song_name}.flac")
    except Exception as e:
        QtWidgets.QMessageBox.critical(None, "错误", f"下载失败: {str(e)}")


class MusicInfoApp(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.song_url = None
        self.song_name = None
        self.init_ui()

        # 创建一个定时器用于延迟处理ID输入
        self.id_input_timer = QtCore.QTimer()
        self.id_input_timer.setSingleShot(True)
        self.id_input_timer.timeout.connect(self.fetch_song_info)

    def on_song_id_changed(self):
        self.id_input_timer.start(1000)

    def init_ui(self):
        self.setWindowTitle("网易云单曲下载工具")
        self.setGeometry(100, 100, 900, 600)
        self.setStyleSheet("background-color: #2E2E2E; color: #FFFFFF;")
        self.setWindowIcon(QtGui.QIcon("163.ico"))

        main_layout = QtWidgets.QHBoxLayout(self)

        left_layout = QtWidgets.QVBoxLayout()

        title_label = QtWidgets.QLabel("网易云单曲下载工具", self)
        title_label.setFont(QtGui.QFont("Helvetica", 22, QtGui.QFont.Bold))
        title_label.setStyleSheet("color: #1DB954; margin-bottom: 20px;")
        title_label.setAlignment(QtCore.Qt.AlignCenter)
        left_layout.addWidget(title_label)

        song_id_card = QtWidgets.QGroupBox("歌曲ID输入", self)
        song_id_card.setStyleSheet("border: 1px solid #1DB954; border-radius: 8px; padding: 10px;")
        song_id_layout = QtWidgets.QHBoxLayout(song_id_card)
        self.song_id_input = QtWidgets.QLineEdit(song_id_card)
        self.song_id_input.setPlaceholderText("请输入歌曲ID")
        self.song_id_input.setStyleSheet("background-color: #404040; color: #FFFFFF; border-radius: 5px; padding: 5px;")
        song_id_layout.addWidget(self.song_id_input)
        left_layout.addWidget(song_id_card)

        quality_cookie_card = QtWidgets.QGroupBox("音质选择与Cookie输入", self)
        quality_cookie_card.setStyleSheet("border: 1px solid #1DB954; border-radius: 8px; padding: 10px;")
        quality_cookie_layout = QtWidgets.QFormLayout(quality_cookie_card)
        self.level_input = QtWidgets.QComboBox(quality_cookie_card)
        self.level_input.addItems(
            ["standard (标准音质)", "exhigh (极高音质)", "lossless (无损音质)", "hires (Hi-Res音质)",
             "jyeffect (高清环绕声)", "sky (沉浸环绕声)", "jymaster (超清母带)"])
        self.level_input.setStyleSheet("background-color: #404040; color: #FFFFFF; border-radius: 5px; padding: 5px;")
        self.cookie_input = QtWidgets.QLineEdit(quality_cookie_card)
        self.cookie_input.setEchoMode(QtWidgets.QLineEdit.Password)
        self.cookie_input.setStyleSheet("background-color: #404040; color: #FFFFFF; border-radius: 5px; padding: 5px;")
        quality_cookie_layout.addRow("请选择音质级别：", self.level_input)
        quality_cookie_layout.addRow("请输入MUSIC_U：", self.cookie_input)
        left_layout.addWidget(quality_cookie_card)

        song_info_card = QtWidgets.QGroupBox("歌曲信息", self)
        song_info_card.setStyleSheet("border: 1px solid #1DB954; border-radius: 8px; padding: 10px;")
        song_info_layout = QtWidgets.QVBoxLayout(song_info_card)
        self.result_text = QtWidgets.QTextEdit(song_info_card)
        self.result_text.setReadOnly(True)
        self.result_text.setStyleSheet("background-color: #333333; color: #FFFFFF; border-radius: 5px;")
        song_info_layout.addWidget(self.result_text)
        left_layout.addWidget(song_info_card)

        button_layout = QtWidgets.QHBoxLayout()
        self.download_button = QtWidgets.QPushButton("下载歌曲", self)
        self.download_button.setStyleSheet(
            "background-color: #1DB954; color: white; border-radius: 10px; padding: 10px 20px;")
        self.download_button.setEnabled(False)
        button_layout.addWidget(self.download_button)
        left_layout.addLayout(button_layout)

        main_layout.addLayout(left_layout)

        lyrics_card = QtWidgets.QGroupBox("歌词", self)
        lyrics_card.setStyleSheet("border: 1px solid #1DB954; border-radius: 8px; padding: 10px;")
        lyrics_layout = QtWidgets.QVBoxLayout(lyrics_card)
        self.lyrics_text = QtWidgets.QTextEdit(lyrics_card)
        self.lyrics_text.setReadOnly(True)
        self.lyrics_text.setStyleSheet("background-color: #333333; color: #FFFFFF; border-radius: 5px;")
        lyrics_layout.addWidget(self.lyrics_text)
        main_layout.addWidget(lyrics_card)

        links_layout = QtWidgets.QHBoxLayout()
        github_label = QtWidgets.QLabel("<a href='https://github.com/Hellohistory/OpenPrepTools'>GitHub地址</a>", self)
        github_label.setStyleSheet("color: #1DB954; margin-top: 20px;")
        github_label.setOpenExternalLinks(True)
        links_layout.addWidget(github_label)

        gitee_label = QtWidgets.QLabel("<a href='https://gitee.com/Hellohistory/OpenPrepTools'>Gitee地址</a>", self)
        gitee_label.setStyleSheet("color: #1DB954; margin-top: 20px; margin-left: 20px;")
        gitee_label.setOpenExternalLinks(True)
        links_layout.addWidget(gitee_label)

        left_layout.addLayout(links_layout)

        self.setLayout(main_layout)

        self.song_id_input.textChanged.connect(self.on_song_id_changed)
        self.download_button.clicked.connect(self.download_song_action)

        self.level_input.currentIndexChanged.connect(self.fetch_song_info)

        self.auto_load_cookie()

    def auto_load_cookie(self):
        cookie = load_cookie()
        if cookie and "MUSIC_U" in cookie:
            self.cookie_input.setText(cookie["MUSIC_U"])

    def fetch_song_info(self):
        song_id = self.song_id_input.text()
        if not song_id:
            QtWidgets.QMessageBox.critical(self, "错误", "歌曲ID不能为空！")
            return

        level = self.level_input.currentText().split()[0]

        music_u = self.cookie_input.text().strip()
        cookies = {
            "os": "pc",
            "appver": "8.9.70",
            "osver": "",
            "deviceId": "pyncm!"
        }
        if music_u:
            cookies["MUSIC_U"] = music_u
            save_cookie(cookies)

        try:
            url_info = url_v1(song_id, level, cookies)
            song_info = name_v1(song_id)
            lyric_info = lyric_v1(song_id, cookies)

            if 'data' in url_info and url_info['data'][0]['url']:
                self.song_url = url_info['data'][0]['url']
                self.song_name = sanitize_filename(song_info['songs'][0]['name'])
                song_lyrics = lyric_info.get('lrc', {}).get('lyric', '无歌词')
                result = f"歌曲名称: {self.song_name}\n歌曲链接: {self.song_url}"
                self.result_text.setText(result)

                self.lyrics_text.setText(song_lyrics)

                self.download_button.setEnabled(True)
            else:
                QtWidgets.QMessageBox.critical(self, "错误", "无法获取歌曲链接信息！")

        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "错误", f"发生错误: {str(e)})")

    def download_song_action(self):
        if self.song_url and self.song_name:
            download_song(self.song_url, self.song_name)
        else:
            QtWidgets.QMessageBox.critical(self, "错误", "无法下载歌曲，请先获取歌曲信息！")


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    music_info_app = MusicInfoApp()
    music_info_app.show()
    sys.exit(app.exec_())
