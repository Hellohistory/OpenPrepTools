# config.py
"""
配置：常量定义
"""
from pathlib import Path

# 本地数据库路径
DB_PATH: Path = Path(__file__).parent / "resources" / "History_Chronology.db"

# 远程数据库下载地址
REMOTE_DB_URL: str = "https://github.com/Hellohistory/OpenPrepTools/blob/master/history_chronology/resources/History_Chronology.db"

# 支持的年份上下限
YEAR_MIN: int = -841
YEAR_MAX: int = 1911

# 各种主题样式表路径
LIGHT_STYLE_QSS: Path = Path(__file__).parent / "resources" / "style.qss"
DARK_STYLE_QSS: Path = Path(__file__).parent / "resources" / "style_dark.qss"
BLUE_STYLE_QSS: Path = Path(__file__).parent / "resources" / "style_blue.qss"
GREEN_STYLE_QSS: Path = Path(__file__).parent / "resources" / "style_green.qss"
ORANGE_STYLE_QSS: Path = Path(__file__).parent / "resources" / "style_orange.qss"
HIGHCONTRAST_STYLE_QSS: Path = Path(__file__).parent / "resources" / "style_highcontrast.qss"
SOLARIZED_STYLE_QSS: Path = Path(__file__).parent / "resources" / "style_solarized.qss"

# 应用程序图标路径
ICON_PATH: Path = Path(__file__).parent / "resources" / "logo.ico"
