"""Vignette d'un média dans le panneau Médias."""

from PyQt6.QtCore import QMimeData, QRectF, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QDrag, QFont, QPainter
from PyQt6.QtWidgets import QApplication, QFrame, QLabel, QSizePolicy, QVBoxLayout, QWidget

from view.painting import draw_image, draw_stripes, draw_waveform
from view.theme import CLIP_COLORS, KIND_ICONS, WHITE, icon

MEDIA_MIME_TYPE = "application/x-clipso-media"


class MediaThumbnail(QWidget):
    def __init__(self, media: dict):
        super().__init__()
        self.media = media
        self.setFixedHeight(66)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def paintEvent(self, _):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = QRectF(self.rect())
        kind = self.media["kind"]

        if kind == "audio":
            background, _, accent = CLIP_COLORS["audio"]
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(background))
            painter.drawRoundedRect(rect, 9, 9)
            peaks = self.media.get("peaks")
            draw_waveform(painter, rect.adjusted(10, 20, -10, -18), QColor(accent), 18, len(self.media["name"]), peaks)
        elif self.media.get("thumbnail") is not None:
            draw_image(painter, rect, self.media["thumbnail"], 9)
        else:
            draw_stripes(painter, rect, QColor(self.media["color"]), 9)

        badge = QRectF(7, 7, 20, 20)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(255, 255, 255, 215))
        painter.drawRoundedRect(badge, 5, 5)
        painter.drawPixmap(badge.adjusted(3, 3, -3, -3).toRect(), icon(KIND_ICONS[kind]).pixmap(28, 28))

        if self.media.get("used"):
            check = QRectF(rect.right() - 25, 7, 18, 18)
            painter.setBrush(QColor(255, 255, 255, 235))
            painter.drawEllipse(check)
            painter.drawPixmap(check.adjusted(3, 3, -3, -3).toRect(), icon("check-bold").pixmap(24, 24))

        if self.media.get("duration"):
            font = QFont("JetBrains Mono", 7)
            font.setWeight(QFont.Weight.Bold)
            painter.setFont(font)
            text = self.media["duration"]
            width = painter.fontMetrics().horizontalAdvance(text) + 10
            box = QRectF(rect.right() - width - 6, rect.bottom() - 21, width, 15)
            painter.setBrush(QColor(43, 42, 40, 215))
            painter.drawRoundedRect(box, 4, 4)
            painter.setPen(QColor(WHITE))
            painter.drawText(box, Qt.AlignmentFlag.AlignCenter, text)


class MediaTile(QFrame):
    activated = pyqtSignal(int)  # index du média

    def __init__(self, media: dict):
        super().__init__()
        self.media = media
        self._press_position = None
        self.setObjectName("mediaTile")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip(media["name"])

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        layout.addWidget(MediaThumbnail(media))
        name = QLabel(media["name"])
        name.setObjectName("mediaName")
        layout.addWidget(name)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._press_position = event.position()

    def mouseMoveEvent(self, event):
        if self._press_position is None:
            return
        if (event.position() - self._press_position).manhattanLength() < QApplication.startDragDistance():
            return
        self._press_position = None
        drag = QDrag(self)
        mime = QMimeData()
        mime.setData(MEDIA_MIME_TYPE, str(self.media["index"]).encode())
        drag.setMimeData(mime)
        drag.setPixmap(self.grab().scaledToWidth(90, Qt.TransformationMode.SmoothTransformation))
        drag.exec(Qt.DropAction.CopyAction)

    def mouseReleaseEvent(self, event):
        self._press_position = None

    def mouseDoubleClickEvent(self, event):
        self.activated.emit(self.media["index"])
