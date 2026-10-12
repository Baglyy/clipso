"""En-tête d'une piste de la timeline (nom, visibilité, verrou)."""

from PyQt6.QtCore import QSize
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QToolButton

from view.theme import INK, KIND_ICONS, MUTED, icon


class TrackHeader(QFrame):
    def __init__(self, track: dict, height: int):
        super().__init__()
        self.setObjectName("trackHeader")
        self.setFixedHeight(height)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 0, 6, 0)
        layout.setSpacing(6)

        kind_icon = QLabel()
        kind_icon.setPixmap(icon(track.get("icon") or KIND_ICONS[track["kind"]]).pixmap(18, 18))
        layout.addWidget(kind_icon)
        name = QLabel(track["name"])
        name.setObjectName("trackName")
        layout.addWidget(name, stretch=1)

        is_audio = track["kind"] == "audio"
        self.visibility_button = self._make_button(
            "speaker-high" if is_audio else "eye",
            "speaker-x" if is_audio else "eye-slash",
            "Couper la piste" if is_audio else "Masquer la piste",
        )
        self.lock_button = self._make_button("lock-simple-open", "lock-simple", "Verrouiller la piste")
        layout.addWidget(self.visibility_button)
        layout.addWidget(self.lock_button)

    def _make_button(self, icon_on: str, icon_off: str, tooltip: str) -> QToolButton:
        button = QToolButton()
        button.setObjectName("trackButton")
        button.setCheckable(True)
        button.setToolTip(tooltip)
        button.setFixedSize(24, 24)
        button.setIconSize(QSize(16, 16))
        button.setIcon(icon(icon_on, MUTED))
        button.toggled.connect(
            lambda checked: button.setIcon(icon(icon_off if checked else icon_on, INK if checked else MUTED))
        )
        return button
