# app.py
"""
应用程序入口
"""

import sys
from pathlib import Path

import requests
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon

from ui.main_window import MainWindow
import config


def download_db(db_path: Path, url: str) -> None:
    response = requests.get(url, stream=True)
    response.raise_for_status()
    with open(db_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)


def main() -> None:
    db_path = Path(config.DB_PATH)
    if not db_path.exists():
        try:
            print(f"数据库文件 {db_path} 不存在，正在从远程下载...")
            download_db(db_path, config.REMOTE_DB_URL)
            print("数据库下载完成。")
        except Exception as e:
            print(f"数据库下载失败：{e}")
            sys.exit(1)
    app = QApplication(sys.argv)
    icon_path = Path(config.ICON_PATH)
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))
    else:
        print(f"警告：应用图标文件未找到：{icon_path}")

    qss_path = config.STYLE_QSS
    if qss_path.exists():
        app.setStyleSheet(qss_path.read_text(encoding="utf-8"))

    win = MainWindow(db_path=str(db_path))
    win.resize(1000, 650)
    win.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
