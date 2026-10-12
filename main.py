import sys

from PyQt6.QtGui import QFontDatabase
from PyQt6.QtWidgets import QApplication

from view.main_window import MainWindow
from view.theme import ASSETS


def load_style(app: QApplication):
    for font_file in (ASSETS / "fonts").glob("*.ttf"):
        QFontDatabase.addApplicationFont(str(font_file))
    style = (ASSETS / "styles" / "clipso.qss").read_text(encoding="utf-8")
    app.setStyleSheet(style.replace("{assets}", ASSETS.as_posix()))


def main():
    app = QApplication(sys.argv)
    load_style(app)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
