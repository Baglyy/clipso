"""Zone d'aperçu vidéo : affiche l'image du montage calculée par le controller."""

from PyQt6.QtCore import QRectF, Qt
from PyQt6.QtGui import QColor, QImage, QPainter, QPainterPath, QPen
from PyQt6.QtWidgets import QSizePolicy, QWidget

from view.theme import GREEN, INK

DEFAULT_ASPECT = 16 / 9
CORNER_RADIUS = 10
SELECTION_MARGIN = 4


class VideoView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMinimumSize(320, 180)
        self.aspect = DEFAULT_ASPECT
        self._image: QImage | None = None
        # en fractions de l'image (0 à 1)
        self._selection: QRectF | None = None

    def set_aspect(self, aspect: float):
        self.aspect = aspect
        self.update()

    def show_image(self, image: QImage | None):
        self._image = image
        self.update()

    def set_selection(self, box: QRectF | None):
        self._selection = box
        self.update()

    def frame_rect(self) -> QRectF:
        """Rectangle au format du projet le plus grand possible, centré."""
        w, h = self.width(), self.height()
        if w / h > self.aspect:
            fw, fh = h * self.aspect, h
        else:
            fw, fh = w, w / self.aspect
        return QRectF((w - fw) / 2, (h - fh) / 2, fw, fh)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        frame = self.frame_rect()

        if self._image is None:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(INK))
            painter.drawRoundedRect(frame, CORNER_RADIUS, CORNER_RADIUS)
        else:
            path = QPainterPath()
            path.addRoundedRect(frame, CORNER_RADIUS, CORNER_RADIUS)
            painter.save()
            painter.setClipPath(path)
            painter.drawImage(frame, self._image)
            painter.restore()

        if self._selection is not None:
            box = QRectF(
                frame.left() + self._selection.x() * frame.width(),
                frame.top() + self._selection.y() * frame.height(),
                self._selection.width() * frame.width(),
                self._selection.height() * frame.height(),
            )
            margin = SELECTION_MARGIN
            painter.setPen(QPen(QColor(GREEN), 1.5, Qt.PenStyle.DashLine))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRect(box.adjusted(-margin, -margin, margin, margin))
