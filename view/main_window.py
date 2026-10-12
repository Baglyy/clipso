from PyQt6.QtCore import QSize
from PyQt6.QtWidgets import QMainWindow, QStackedWidget

from view import demo_data
from view.dialogs.export_dialog import ExportDialog
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

        # TODO: données de démo (demo_data) et clip « logo_club.png » sélectionné d'office, à fournir par le controller
        for project in demo_data.RECENT_PROJECTS:
            item = self.home_page.add_recent_project(*project)
            item.open_requested.connect(self.show_editor)
        self.editor_page.load_project(
            "Vacances à Biarritz", demo_data.MEDIA, demo_data.TRACKS, demo_data.DURATION, demo_data.PLAYHEAD
        )
        self.editor_page.select_clip(demo_data.SELECTED_CLIP, tab=demo_data.SELECTED_TAB)

        # TODO: « Créer » et « Ouvrir » affichent directement l'éditeur de démo, sans créer ni ouvrir de projet
        self.home_page.createProjectButton.clicked.connect(self.show_editor)
        self.home_page.openProjectButton.clicked.connect(self.show_editor)
        self.editor_page.home_requested.connect(self.show_home)
        self.editor_page.export_requested.connect(self.show_export)

    def show_home(self):
        self.pages.setCurrentWidget(self.home_page)

    def show_editor(self):
        self.pages.setCurrentWidget(self.editor_page)

    def show_export(self):
        ExportDialog(self).exec()
