# config.py
"""
配置：常量定义
"""
from pathlib import Path

# 本地数据库路径（相对于项目根目录）
DB_PATH: Path = Path(__file__).parent / "History_Chronology.db"

# 远程数据库下载地址
REMOTE_DB_URL: str = "https://example.com/databases/History_Chronology.db"

# 支持的年份上下限
YEAR_MIN: int = -841
YEAR_MAX: int = 1911

# QSS 样式文件路径
STYLE_QSS: Path = Path(__file__).parent / "resources" / "style.qss"
ICON_PATH: Path = Path(__file__).parent / "resources" / "logo.ico"
