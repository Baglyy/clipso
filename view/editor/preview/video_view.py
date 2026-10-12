"""Zone d'aperçu vidéo : affiche l'image courante et les calques (texte, logo)."""

from PyQt6.QtCore import QRectF, Qt
from PyQt6.QtGui import QColor, QFont, QPainter, QPen
from PyQt6.QtWidgets import QSizePolicy, QWidget

from view.painting import draw_stripes
from view.theme import GREEN, INK, WHITE

# TODO: format 16:9 en dur, à lire depuis le projet (9:16, 1:1…)
ASPECT = 16 / 9


class VideoView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMinimumSize(320, 180)
        # TODO: image initiale de démo (coucher_soleil.mp4 + logo), à retirer
        self._color = "#AE7657"
        self._source = "coucher_soleil.mp4"
        self._text = ""
        self._logo = True
        self._logo_selected = True

    def show_frame(self, color: str, source: str, text: str = "", logo: bool = False, logo_selected: bool = False):
        self._color, self._source, self._text = color, source, text
        self._logo, self._logo_selected = logo, logo_selected
        self.update()

    def frame_rect(self) -> QRectF:
        """Rectangle 16:9 le plus grand possible, centré."""
        w, h = self.width(), self.height()
        if w / h > ASPECT:
            fw, fh = h * ASPECT, h
        else:
            fw, fh = w, w / ASPECT
        return QRectF((w - fw) / 2, (h - fh) / 2, fw, fh)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        frame = self.frame_rect()

        # TODO: rayures colorées à la place de la vraie image vidéo décodée
        if self._color:
            draw_stripes(painter, frame, QColor(self._color).lighter(108), 10)
        else:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(INK))
            painter.drawRoundedRect(frame, 10, 10)

        if self._source:
            font = QFont("JetBrains Mono", 8)
            font.setWeight(QFont.Weight.Medium)
            painter.setFont(font)
            label = f"aperçu vidéo · {self._source}"
            text_width = painter.fontMetrics().horizontalAdvance(label)
            chip = QRectF(frame.left() + 10, frame.top() + 9, text_width + 16, 20)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(43, 42, 40, 150))
            painter.drawRoundedRect(chip, 5, 5)
            painter.setPen(QColor(WHITE))
            painter.drawText(chip, Qt.AlignmentFlag.AlignCenter, label)

        # TODO: logo simulé par un cercle « logo_club » à position fixe, à remplacer par l'image réelle et sa position
        if self._logo:
            diameter = frame.height() * 0.29
            center_x = frame.left() + frame.width() * 0.84
            center_y = frame.top() + frame.height() * 0.18
            circle = QRectF(center_x - diameter / 2, center_y - diameter / 2, diameter, diameter)
            if self._logo_selected:
                pen = QPen(QColor(GREEN), 1.5, Qt.PenStyle.DashLine)
                painter.setPen(pen)
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.drawEllipse(circle.adjusted(-6, -6, 6, 6))
            painter.setPen(QPen(QColor(INK), 3))
            painter.setBrush(QColor("#F4F2EE"))
            painter.drawEllipse(circle)
            painter.setPen(QColor(INK))
            painter.setFont(QFont("JetBrains Mono", 7))
            painter.drawText(circle, Qt.AlignmentFlag.AlignCenter, "logo_club")

        if self._text:
            font = QFont("Nunito", max(12, int(frame.height() * 0.085)))
            font.setWeight(QFont.Weight.Black)
            painter.setFont(font)
            painter.setPen(QColor(WHITE))
            area = QRectF(frame.left(), frame.top() + frame.height() * 0.66, frame.width(), frame.height() * 0.2)
            painter.drawText(area, Qt.AlignmentFlag.AlignCenter, self._text)
