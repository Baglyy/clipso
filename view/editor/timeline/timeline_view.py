"""Timeline : règle des temps, pistes, clips et tête de lecture."""

from PyQt6.QtCore import QPointF, QRectF, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QFontMetrics, QPainter, QPainterPath, QPen
from PyQt6.QtWidgets import QSizePolicy, QWidget

from view.format import mm_ss, seconds_text
from view.painting import draw_waveform
from view.theme import CLIP_COLORS, GREEN, INK, KIND_ICONS, MUTED, ROW, WHITE, icon, mix

RULER_HEIGHT = 28
TRACK_GAP = 7
TRACK_HEIGHTS = {"overlay": 42, "video": 62, "audio": 42}
LEFT_MARGIN = 4
SIDE_MARGINS = 12
# intervalles possibles entre deux graduations de la règle, en secondes
RULER_STEPS = (1, 2, 5, 10, 15, 30, 60, 120, 300, 600)
MIN_LABEL_SPACING = 48
MIN_TICK_SPACING = 8
# en dessous de cette largeur, un clip n'affiche pas sa durée
MIN_WIDTH_FOR_DURATION = 90


class TimelineView(QWidget):
    position_changed = pyqtSignal(float)
    clip_selected = pyqtSignal(dict, dict)
    content_width_changed = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMinimumHeight(RULER_HEIGHT + 3 * 42)
        self.setMouseTracking(True)
        self.tracks: list[dict] = []
        self.duration = 0.0
        self.position = 0.0
        self.selected = None
        self.zoom = 1.0
        self.offset = 0
        self._dragging_playhead = False

    def set_tracks(self, tracks: list[dict], duration: float):
        self.tracks, self.duration = tracks, duration
        self.content_width_changed.emit(self.content_width())
        self.update()

    def set_position(self, seconds: float):
        self.position = max(0.0, min(seconds, self.duration))
        self.update()

    def set_zoom(self, zoom: float):
        self.zoom = zoom
        self.content_width_changed.emit(self.content_width())
        self.update()

    def set_offset(self, offset: int):
        self.offset = offset
        self.update()

    def select(self, track: dict, clip: dict):
        self.selected = clip
        self.update()
        self.clip_selected.emit(track, clip)

    def clips_at(self, seconds: float) -> list[tuple[dict, dict]]:
        return [
            (track, clip)
            for track in self.tracks
            for clip in track["clips"]
            if clip["start"] <= seconds < clip["start"] + clip["duration"]
        ]

    def pixels_per_second(self) -> float:
        """Au zoom 1, tout le projet tient dans la largeur visible."""
        return (self.width() - SIDE_MARGINS) / max(self.duration, 1) * self.zoom

    def content_width(self) -> int:
        return int(self.duration * self.pixels_per_second()) + SIDE_MARGINS

    def x_for(self, seconds: float) -> float:
        return LEFT_MARGIN + seconds * self.pixels_per_second() - self.offset

    def seconds_for(self, x: float) -> float:
        return (x - LEFT_MARGIN + self.offset) / self.pixels_per_second()

    def _ruler_step(self, min_spacing: float) -> int:
        """Plus petit intervalle de RULER_STEPS espacé d'au moins min_spacing pixels."""
        pps = self.pixels_per_second()
        return next((step for step in RULER_STEPS if step * pps >= min_spacing), RULER_STEPS[-1])

    def track_rects(self):
        y = RULER_HEIGHT + TRACK_GAP
        for track in self.tracks:
            height = TRACK_HEIGHTS[track["kind"]]
            yield track, QRectF(0, y, self.width(), height)
            y += height + TRACK_GAP

    def clip_rect(self, clip: dict, row: QRectF) -> QRectF:
        left = self.x_for(clip["start"])
        right = self.x_for(clip["start"] + clip["duration"])
        return QRectF(left + 1, row.top() + 1, right - left - 3, row.height() - 2)

    def mousePressEvent(self, event):
        pos = event.position()
        if pos.y() < RULER_HEIGHT:
            self._dragging_playhead = True
            self._move_playhead(pos.x())
            return
        for track, row in self.track_rects():
            for clip in track["clips"]:
                if self.clip_rect(clip, row).contains(pos):
                    self.select(track, clip)
                    return
        self._dragging_playhead = True
        self._move_playhead(pos.x())

    def mouseMoveEvent(self, event):
        if self._dragging_playhead:
            self._move_playhead(event.position().x())

    def mouseReleaseEvent(self, event):
        self._dragging_playhead = False

    def resizeEvent(self, event):
        self.content_width_changed.emit(self.content_width())

    def _move_playhead(self, x: float):
        self.set_position(self.seconds_for(x))
        self.position_changed.emit(self.position)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        self._paint_ruler(painter)
        for track, row in self.track_rects():
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(ROW))
            painter.drawRoundedRect(row, 10, 10)
            painter.save()
            painter.setClipRect(row)
            for clip in track["clips"]:
                self._paint_clip(painter, clip, self.clip_rect(clip, row))
            painter.restore()
        self._paint_playhead(painter)

    def _paint_ruler(self, painter: QPainter):
        font = QFont("JetBrains Mono", 7)
        font.setWeight(QFont.Weight.Medium)
        painter.setFont(font)
        end = int(self.duration) + 1

        painter.setPen(QPen(QColor("#D2CEC5"), 1))
        for second in range(0, end, self._ruler_step(MIN_TICK_SPACING)):
            x = self.x_for(second)
            painter.drawLine(QPointF(x, RULER_HEIGHT - 5), QPointF(x, RULER_HEIGHT - 1))

        for second in range(0, end, self._ruler_step(MIN_LABEL_SPACING)):
            x = self.x_for(second)
            if not -40 < x < self.width() + 40:
                continue
            painter.setPen(QPen(QColor("#B9B4AA"), 1))
            painter.drawLine(QPointF(x, RULER_HEIGHT - 10), QPointF(x, RULER_HEIGHT - 1))
            painter.setPen(QColor(MUTED))
            painter.drawText(QPointF(x + 1, 11), mm_ss(second))

    def _paint_clip(self, painter: QPainter, clip: dict, rect: QRectF):
        kind = clip["kind"]
        selected = clip is self.selected
        if kind == "video":
            background = mix(clip["color"], WHITE, 0.78)
            border = mix(clip["color"], WHITE, 0.6)
        else:
            background, border, _ = (QColor(c) for c in CLIP_COLORS[kind])

        painter.setPen(QPen(QColor(GREEN) if selected else border, 2 if selected else 1))
        painter.setBrush(background)
        painter.drawRoundedRect(rect, 8, 8)

        self._paint_clip_header(painter, clip, rect)
        self._paint_clip_body(painter, clip, rect)

    def _paint_clip_header(self, painter: QPainter, clip: dict, rect: QRectF):
        """Icône, nom et durée (si le clip est assez large)."""
        kind = clip["kind"]
        header = QRectF(rect.left() + 8, rect.top() + 3, rect.width() - 16, 16)
        painter.drawPixmap(
            QRectF(header.left(), header.top() + 2, 12, 12).toRect(), icon(KIND_ICONS[kind]).pixmap(24, 24)
        )
        name_font = QFont("Nunito", 8)
        name_font.setWeight(QFont.Weight.ExtraBold)
        painter.setFont(name_font)
        painter.setPen(QColor(INK))
        duration_text = seconds_text(clip["duration"])
        mono = QFont("JetBrains Mono", 7)
        show_duration = rect.width() > MIN_WIDTH_FOR_DURATION
        duration_width = QFontMetrics(mono).horizontalAdvance(duration_text) + 12 if show_duration else 0
        name_rect = header.adjusted(17, 0, -duration_width, 0)
        name_width = int(max(0, name_rect.width()))
        name = painter.fontMetrics().elidedText(clip["name"], Qt.TextElideMode.ElideRight, name_width)
        painter.drawText(name_rect, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, name)
        if show_duration:
            painter.setFont(mono)
            painter.setPen(QColor(MUTED))
            painter.drawText(header, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight, duration_text)

    def _paint_clip_body(self, painter: QPainter, clip: dict, rect: QRectF):
        """Images (vidéo), forme d'onde (audio) ou texte, selon le type de clip."""
        kind = clip["kind"]
        body = QRectF(rect.left() + 4, rect.top() + 21, rect.width() - 8, rect.height() - 25)
        if kind == "video":
            self._paint_frames(painter, body, QColor(clip["color"]))
        elif kind == "audio":
            bars = max(8, int(body.width() / 5))
            accent = QColor(CLIP_COLORS["audio"][2])
            draw_waveform(painter, body.adjusted(4, 2, -4, -2), accent, bars, seed=len(clip["name"]))
        elif kind == "text":
            italic = QFont("Nunito", 8)
            italic.setItalic(True)
            painter.setFont(italic)
            painter.setPen(QColor(CLIP_COLORS["text"][2]))
            painter.drawText(
                body.adjusted(4, 0, 0, 0),
                Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
                f"« {clip.get('text', '')} »",
            )

    def _paint_frames(self, painter: QPainter, body: QRectF, color: QColor):
        path = QPainterPath()
        path.addRoundedRect(body, 5, 5)
        painter.save()
        painter.setClipPath(path, Qt.ClipOperation.IntersectClip)
        painter.fillRect(body, color)
        painter.setPen(QPen(QColor(255, 255, 255, 110), 1.5))
        x = body.left() + 44
        while x < body.right():
            painter.drawLine(QPointF(x, body.top()), QPointF(x, body.bottom()))
            x += 44
        painter.restore()

    def _paint_playhead(self, painter: QPainter):
        x = self.x_for(self.position)
        if not -10 < x < self.width() + 10:
            return
        painter.setPen(QPen(QColor(GREEN), 2))
        painter.drawLine(QPointF(x, 6), QPointF(x, self.height()))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(GREEN))
        painter.drawRoundedRect(QRectF(x - 6, 2, 12, 20), 6, 6)
