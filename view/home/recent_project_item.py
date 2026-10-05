"""Une ligne de la liste « Projets récents » de la page d'accueil."""

from PyQt6.QtCore import QSize, Qt, pyqtSignal
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QToolButton, QVBoxLayout

from view.theme import icon


class RecentProjectItem(QFrame):
    open_requested = pyqtSignal()
    more_requested = pyqtSignal()

    def __init__(self, title: str, meta: str, duration: str, color: str):
        super().__init__()
        self.setObjectName("recentProjectItem")
        self.setAttribute(Qt.WidgetAttribute.WA_Hover)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(92)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(9, 9, 16, 9)
        layout.setSpacing(16)

        thumbnail = QLabel()
        thumbnail.setObjectName("projectThumbnail")
        thumbnail.setFixedSize(132, 74)
        thumbnail.setStyleSheet(f"background: {color}; border-radius: 9px;")
        badge_layout = QVBoxLayout(thumbnail)
        badge_layout.setContentsMargins(0, 0, 6, 6)
        badge = QLabel(duration)
        badge.setObjectName("projectDuration")
        badge_layout.addWidget(badge, alignment=Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignBottom)
        layout.addWidget(thumbnail)

        texts = QVBoxLayout()
        texts.setSpacing(2)
        texts.addStretch()
        title_label = QLabel(title)
        title_label.setObjectName("projectTitle")
        meta_label = QLabel(meta)
        meta_label.setObjectName("projectMeta")
        texts.addWidget(title_label)
        texts.addWidget(meta_label)
        texts.addStretch()
        layout.addLayout(texts, stretch=1)

        more_button = self._make_button("projectMoreButton", "dots-three-bold", "Plus d'actions")
        more_button.clicked.connect(self.more_requested)
        layout.addWidget(more_button)

        open_button = self._make_button("projectOpenButton", "caret-right-bold", "Ouvrir")
        open_button.clicked.connect(self.open_requested)
        layout.addWidget(open_button)

    def _make_button(self, name: str, icon_name: str, tooltip: str) -> QToolButton:
        button = QToolButton()
        button.setObjectName(name)
        button.setIcon(icon(icon_name))
        button.setIconSize(QSize(18, 18))
        button.setFixedSize(32, 32)
        button.setToolTip(tooltip)
        return button

    def mouseReleaseEvent(self, event):
        """Un clic n'importe où sur la ligne ouvre le projet."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.open_requested.emit()
        super().mouseReleaseEvent(event)
