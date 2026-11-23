from PyQt6.QtCore import QSize
from PyQt6.QtWidgets import QMainWindow, QStackedWidget

from view.editor.editor_page import EditorPage
from view.home.home_page import HomePage


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Clipso")
        self.resize(QSize(1440, 860))
        self.setMinimumSize(QSize(1100, 700))

        self.home_page = HomePage()
        self.editor_page = EditorPage()
        self.pages = QStackedWidget()
        self.pages.addWidget(self.home_page)
        self.pages.addWidget(self.editor_page)
        self.setCentralWidget(self.pages)

        self.editor_page.home_requested.connect(self.show_home)

    def show_home(self):
        self.pages.setCurrentWidget(self.home_page)

    def show_editor(self):
        self.pages.setCurrentWidget(self.editor_page)
