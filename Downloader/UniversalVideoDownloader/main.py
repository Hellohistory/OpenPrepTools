import sys
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QFont
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton,
    QComboBox, QFileDialog, QMessageBox, QHBoxLayout, QProgressBar, QSpacerItem, QSizePolicy
)
import requests
from core import SignatureGenerator


class VideoDownloader(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.api = SignatureGenerator()
        self.video_data = None

    def init_ui(self):
        self.setWindowTitle("万能视频下载器")
        self.setGeometry(100, 100, 800, 600)
        self.setStyleSheet(self.get_stylesheet())

        # 主布局
        main_layout = QVBoxLayout()

        # 标题部分
        title_layout = QVBoxLayout()
        title = QLabel("🎥 万能视频下载器")
        title.setFont(QFont("Arial", 24, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #ffffff; padding: 20px 0;")
        title_layout.addWidget(title)
        title_layout.setContentsMargins(0, 0, 0, 20)
        main_layout.addLayout(title_layout)

        # 链接输入区域
        input_layout = QHBoxLayout()
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("粘贴视频链接到此处...")
        self.url_input.setFixedHeight(40)
        self.url_input.setStyleSheet("font-size: 16px;")
        self.fetch_button = QPushButton("获取视频信息")
        self.fetch_button.setFixedHeight(40)
        self.fetch_button.setStyleSheet("font-size: 16px;")
        self.fetch_button.clicked.connect(self.fetch_video_info)
        input_layout.addWidget(self.url_input, 3)
        input_layout.addWidget(self.fetch_button, 1)
        main_layout.addLayout(input_layout)

        # 信息展示区域
        info_layout = QHBoxLayout()
        self.cover_label = QLabel()
        self.cover_label.setFixedSize(200, 200)
        self.cover_label.setAlignment(Qt.AlignCenter)
        self.cover_label.setStyleSheet("border: 1px solid #ccc; background: #ffffff;")
        info_layout.addWidget(self.cover_label)

        self.description_label = QLabel("视频简介：暂无")
        self.description_label.setWordWrap(True)
        self.description_label.setStyleSheet("font-size: 16px; color: #ffffff; padding: 10px;")
        info_layout.addWidget(self.description_label)
        main_layout.addLayout(info_layout)

        # 选择质量和下载按钮
        quality_layout = QHBoxLayout()
        self.quality_combo = QComboBox()
        self.quality_combo.setFixedHeight(40)
        self.quality_combo.setStyleSheet("font-size: 16px;")
        self.download_button = QPushButton("下载视频")
        self.download_button.setFixedHeight(40)
        self.download_button.setStyleSheet("font-size: 16px;")
        self.download_button.clicked.connect(self.download_video)
        quality_layout.addWidget(self.quality_combo, 3)
        quality_layout.addWidget(self.download_button, 1)
        main_layout.addLayout(quality_layout)

        # 下载进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedHeight(30)
        self.progress_bar.setTextVisible(False)
        main_layout.addWidget(self.progress_bar)

        # 空间调整
        main_layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))

        self.setLayout(main_layout)

    def get_stylesheet(self):
        return """
            QWidget {
                background-color: #1e1e2e;
                color: #ffffff;
            }
            QLineEdit {
                border: 1px solid #888;
                border-radius: 8px;
                padding: 8px 12px;
                background-color: #2e2e3e;
                color: #ffffff;
            }
            QPushButton {
                background-color: #0078d4;
                color: white;
                border-radius: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #005bb5;
            }
            QComboBox {
                border: 1px solid #888;
                border-radius: 8px;
                padding: 6px;
                background-color: #2e2e3e;
                color: #ffffff;
            }
            QProgressBar {
                border: 1px solid #888;
                border-radius: 8px;
                background: #2e2e3e;
            }
            QProgressBar::chunk {
                background-color: #4caf50;
                border-radius: 8px;
            }
        """

    def fetch_video_info(self):
        url = self.url_input.text()
        if not url:
            QMessageBox.warning(self, "错误", "请输入视频链接！")
            return

        try:
            self.video_data = self.api.send_request(url)
            cover_url = self.video_data.get("cover")
            self.update_cover(cover_url)
            self.update_quality_options()
            self.update_description()
            QMessageBox.information(self, "成功", "视频信息获取成功！")
        except Exception as e:
            QMessageBox.critical(self, "错误", str(e))

    def update_cover(self, cover_url):
        if cover_url:
            response = requests.get(cover_url)
            pixmap = QPixmap()
            pixmap.loadFromData(response.content)
            self.cover_label.setPixmap(pixmap.scaled(200, 200, Qt.KeepAspectRatio))

    def update_description(self):
        description = self.video_data.get("title", "无简介")
        self.description_label.setText(f"视频简介：{description}")

    def update_quality_options(self):
        self.quality_combo.clear()
        videos = self.video_data.get("videos", [])
        for video in videos:
            quality = video.get("quality", "未知")
            size = video.get("size", 0)
            size_mb = f"{size / (1024 * 1024):.2f} MB"
            self.quality_combo.addItem(f"{quality} ({size_mb})", video["url"])

    def download_video(self):
        selected_index = self.quality_combo.currentIndex()
        if selected_index == -1:
            QMessageBox.warning(self, "错误", "请选择视频质量！")
            return

        video_url = self.quality_combo.itemData(selected_index)
        save_path, _ = QFileDialog.getSaveFileName(self, "保存视频", "video.mp4", "视频文件 (*.mp4)")
        if not save_path:
            return

        try:
            response = requests.get(video_url, stream=True)
            total_size = int(response.headers.get("content-length", 0))
            downloaded_size = 0

            with open(save_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=1024):
                    if chunk:
                        f.write(chunk)
                        downloaded_size += len(chunk)
                        progress = int((downloaded_size / total_size) * 100)
                        self.progress_bar.setValue(progress)
            QMessageBox.information(self, "成功", "视频下载成功！")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"视频下载失败：{str(e)}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    downloader = VideoDownloader()
    downloader.show()
    sys.exit(app.exec())
