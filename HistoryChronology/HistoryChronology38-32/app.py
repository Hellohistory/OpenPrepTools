# app.py
"""
应用程序入口
"""

import sys
from pathlib import Path

import requests
from PySide2.QtWidgets import QApplication
from PySide2.QtGui import QIcon

from main_window import MainWindow
import config


def download_db(db_path: Path, url: str) -> None:
    """
    下载数据库文件到本地，如果文件不存在则从远程获取
    :param db_path: 本地数据库文件路径
    :param url: 远程数据库下载地址
    """
    response = requests.get(url, stream=True)
    response.raise_for_status()
    with open(db_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)


def main() -> None:
    """
    应用程序主入口，检查数据库、加载样式、创建并运行主窗口
    """
    db_path = Path(config.DB_PATH)
    if not db_path.exists():
        try:
            print(f"数据库文件 {db_path} 不存在，正在从远程下载...")
            download_db(db_path, config.REMOTE_DB_URL)
            print("数据库下载完成。")
        except Exception as e:
            print(f"数据库下载失败：{e}")
            sys.exit(1)

    # 创建 Qt 应用实例
    app = QApplication(sys.argv)

    # 设置应用图标
    icon_path = Path(config.ICON_PATH)
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))
    else:
        print(f"警告：应用图标文件未找到：{icon_path}")

    # 加载 QSS 样式
    qss_path = Path(config.LIGHT_STYLE_QSS)
    if qss_path.exists():
        app.setStyleSheet(qss_path.read_text(encoding="utf-8"))

    # 创建并显示主窗口
    win = MainWindow(db_path=str(db_path))
    win.resize(1000, 650)
    win.show()

    # 进入主循环
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
