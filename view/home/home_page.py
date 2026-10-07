"""Page d'accueil : nouveau projet + projets récents."""

from pathlib import Path

from PyQt6 import uic
from PyQt6.QtCore import QRectF, QSize, Qt
from PyQt6.QtGui import QColor, QPainter, QPen, QPixmap
from PyQt6.QtWidgets import QLabel, QLineEdit, QToolButton, QVBoxLayout, QWidget

from view.home.recent_project_item import RecentProjectItem
from view.theme import ASSETS, INK, MUTED, WHITE, icon
from view.ui_helpers import clickable, setup_button


class HomePage(QWidget):
    def __init__(self):
        super().__init__()
        uic.loadUi(Path(__file__).parent / "home_page.ui", self)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground)
        # TODO: greetingTitleLabel (« Bonjour Léa ! ») et avatarButton (« L ») sont figés dans home_page.ui
        self._setup_images()
        self._setup_icons()
        self._setup_format_buttons()

    def _setup_images(self):
        logo = QPixmap(str(ASSETS / "images" / "logo.png"))
        self.logoLabel.setPixmap(
            logo.scaled(36, 36, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        )
        mascot = QPixmap(str(ASSETS / "images" / "mascot.png"))
        self.mascotLabel.setPixmap(
            mascot.scaled(
                self.mascotLabel.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
            )
        )

    def _setup_icons(self):
        setup_button(self.helpButton, "question", size=22)
        setup_button(self.settingsButton, "gear-six", size=22)
        self.newProjectIconLabel.setPixmap(icon("plus-bold", WHITE).pixmap(22, 22))

        setup_button(self.createProjectButton, "caret-double-right-bold", color=WHITE)
        # icône à droite du texte
        self.createProjectButton.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        self.openProjectButton.setIcon(icon("folder-open"))
        self.importMediaButton.setIcon(icon("upload-simple"))
        clickable(self.openProjectButton, self.importMediaButton)

        self.searchProjectEdit.addAction(icon("magnifying-glass", MUTED), QLineEdit.ActionPosition.LeadingPosition)

    def _setup_format_buttons(self):
        formats = (
            (self.formatLandscapeButton, (70, 38), "Paysage", "16:9 · YouTube"),
            (self.formatVerticalButton, (32, 56), "Vertical", "9:16 · Réseaux"),
            (self.formatSquareButton, (46, 46), "Carré", "1:1 · Publication"),
        )
        for button, shape, title, subtitle in formats:
            self._decorate_format_button(button, shape, title, subtitle)

    def _decorate_format_button(self, button: QToolButton, shape, title: str, subtitle: str):
        """Place une icône et deux lignes de texte (styles différents) dans le bouton."""
        clickable(button)
        layout = QVBoxLayout(button)
        layout.setContentsMargins(8, 16, 8, 12)
        layout.setSpacing(2)

        shape_label = QLabel()
        shape_label.setPixmap(_format_pixmap(*shape))
        shape_label.setObjectName("formatShape")
        title_label = QLabel(title)
        title_label.setObjectName("formatTitle")
        subtitle_label = QLabel(subtitle)
        subtitle_label.setObjectName("formatSubtitle")

        for label in (shape_label, title_label, subtitle_label):
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        layout.addWidget(shape_label, stretch=1)
        layout.addWidget(title_label)
        layout.addWidget(subtitle_label)

    def add_recent_project(self, title: str, meta: str, duration: str, color: str) -> RecentProjectItem:
        """Ajoute une ligne à la liste (appelé par le controller)."""
        item = RecentProjectItem(title, meta, duration, color)
        layout = self.recentProjectsLayout
        layout.insertWidget(layout.count() - 1, item)
        return item


def _format_pixmap(width: int, height: int) -> QPixmap:
    """Dessine un rectangle arrondi qui représente le format (16:9, 9:16, 1:1)."""
    size = QSize(76, 60)
    pixmap = QPixmap(size)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setPen(QPen(QColor(INK), 3))
    rect = QRectF((size.width() - width) / 2, (size.height() - height) / 2, width, height)
    painter.drawRoundedRect(rect, 7, 7)
    painter.end()
    return pixmap
