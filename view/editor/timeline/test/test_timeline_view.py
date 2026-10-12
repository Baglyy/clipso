import pytest
from PyQt6.QtCore import QPoint, Qt

# Adapter l'import selon l'arborescence de votre projet
from view.editor.timeline.timeline_view import RULER_HEIGHT, TimelineView


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_tracks():
    """Jeu de données représentatif de pistes (vidéo, audio, texte/overlay)."""
    return [
        {
            "name": "Piste Vidéo",
            "kind": "video",
            "clips": [
                {"name": "intro.mp4", "kind": "video", "start": 0.0, "duration": 5.0, "color": "#3498DB"},
                {"name": "outro.mp4", "kind": "video", "start": 6.0, "duration": 4.0, "color": "#2ECC71"},
            ],
        },
        {
            "name": "Piste Audio",
            "kind": "audio",
            "clips": [
                {"name": "musique.mp3", "kind": "audio", "start": 0.0, "duration": 10.0},
            ],
        },
        {
            "name": "Sous-titres",
            "kind": "overlay",
            "clips": [
                {"name": "Titre", "kind": "text", "start": 1.0, "duration": 3.0, "text": "Bienvenue"},
            ],
        },
    ]


@pytest.fixture
def timeline(qtbot, sample_tracks):
    """Fixture créant une TimelineView initialisée et dimensionnée."""
    widget = TimelineView()
    qtbot.addWidget(widget)
    widget.resize(800, 300)
    widget.set_tracks(sample_tracks, duration=10.0)
    return widget


# ---------------------------------------------------------------------------
# Tests : État initial et Configuration
# ---------------------------------------------------------------------------

def test_initial_state(qtbot):
    """Vérifie les valeurs par défaut d'une timeline vide."""
    view = TimelineView()
    qtbot.addWidget(view)

    assert view.tracks == []
    assert view.duration == 0.0
    assert view.position == 0.0
    assert view.selected is None
    assert view.zoom == 1.0
    assert view.offset == 0
    assert not view._dragging_playhead
    assert view.minimumHeight() >= RULER_HEIGHT + 3 * 42


def test_set_tracks_emits_content_width_changed(qtbot, sample_tracks):
    """Vérifie que set_tracks met à jour les données et émet le signal content_width_changed."""
    view = TimelineView()
    qtbot.addWidget(view)
    view.resize(800, 300)

    with qtbot.waitSignal(view.content_width_changed, timeout=1000) as blocker:
        view.set_tracks(sample_tracks, duration=15.0)

    assert view.tracks == sample_tracks
    assert view.duration == 15.0
    assert blocker.args[0] == view.content_width()


# ---------------------------------------------------------------------------
# Tests : Tête de lecture et Bornes de Position
# ---------------------------------------------------------------------------

def test_set_position_clamps_within_bounds(timeline):
    """Vérifie que la position reste obligatoirement comprise entre 0 et duration."""
    timeline.set_position(5.0)
    assert timeline.position == 5.0

    # Dépassement vers le bas
    timeline.set_position(-3.0)
    assert timeline.position == 0.0

    # Dépassement vers le haut
    timeline.set_position(25.0)
    assert timeline.position == 10.0


# ---------------------------------------------------------------------------
# Tests : Conversions Coordonnées <-> Temps
# ---------------------------------------------------------------------------

def test_time_and_pixel_conversions(timeline):
    """Vérifie la réciprocité des méthodes x_for et seconds_for."""
    for sec in (0.0, 2.5, 7.0, 10.0):
        x = timeline.x_for(sec)
        calculated_sec = timeline.seconds_for(x)
        assert calculated_sec == pytest.approx(sec, rel=1e-5)


def test_zoom_and_offset_impact(timeline, qtbot):
    """Vérifie l'impact du zoom et de l'offset sur les positions et la largeur totale."""
    initial_x = timeline.x_for(5.0)

    # Déplacement via offset
    timeline.set_offset(50)
    assert timeline.offset == 50
    assert timeline.x_for(5.0) == initial_x - 50

    # Zoom
    with qtbot.waitSignal(timeline.content_width_changed, timeout=1000):
        timeline.set_zoom(2.0)
    assert timeline.zoom == 2.0


# ---------------------------------------------------------------------------
# Tests : Recherche et Sélection de Clips
# ---------------------------------------------------------------------------

def test_clips_at_timestamp(timeline):
    """Vérifie la recherche des clips actifs à un instant T."""
    # À 2.0s : intro.mp4 (vidéo), musique.mp3 (audio) et Titre (overlay) sont actifs
    clips_at_2 = timeline.clips_at(2.0)
    clip_names = [clip["name"] for _, clip in clips_at_2]
    assert len(clips_at_2) == 3
    assert set(clip_names) == {"intro.mp4", "musique.mp3", "Titre"}

    # À 5.5s : seul musique.mp3 est actif (entre intro et outro)
    clips_at_5_5 = timeline.clips_at(5.5)
    assert len(clips_at_5_5) == 1
    assert clips_at_5_5[0][1]["name"] == "musique.mp3"

    # En dehors de la timeline
    assert timeline.clips_at(15.0) == []


def test_select_clip_emits_signal(timeline, sample_tracks, qtbot):
    """Vérifie que la méthode select met à jour l'élément sélectionné et émet le signal."""
    target_track = sample_tracks[0]
    target_clip = target_track["clips"][0]

    with qtbot.waitSignal(timeline.clip_selected, timeout=1000) as blocker:
        timeline.select(target_track, target_clip)

    assert timeline.selected is target_clip
    assert blocker.args == [target_track, target_clip]


# ---------------------------------------------------------------------------
# Tests : Interactions Souris
# ---------------------------------------------------------------------------

def test_click_on_ruler_moves_playhead(timeline, qtbot):
    """Vérifie qu'un clic dans la règle déplace la tête de lecture et émet position_changed."""
    # Hauteur de la règle < RULER_HEIGHT (28px)
    target_x = 200
    expected_seconds = timeline.seconds_for(target_x)

    with qtbot.waitSignal(timeline.position_changed, timeout=1000) as blocker:
        qtbot.mouseClick(timeline, Qt.MouseButton.LeftButton, pos=QPoint(target_x, 10))

    assert timeline.position == pytest.approx(expected_seconds, rel=1e-3)
    assert blocker.args[0] == pytest.approx(expected_seconds, rel=1e-3)


def test_click_on_clip_selects_it(timeline, sample_tracks, qtbot):
    """Vérifie qu'un clic sur un clip sélectionne le clip et émet clip_selected."""
    target_track, row = next(timeline.track_rects())
    target_clip = target_track["clips"][0]
    clip_rect = timeline.clip_rect(target_clip, row)

    # Clic au centre du clip
    click_pos = clip_rect.center().toPoint()
    with qtbot.waitSignal(timeline.clip_selected, timeout=1000) as blocker:
        qtbot.mouseClick(timeline, Qt.MouseButton.LeftButton, pos=click_pos)

    assert timeline.selected is target_clip
    assert blocker.args == [target_track, target_clip]


def test_drag_playhead(timeline, qtbot):
    """Vérifie le suivi du curseur lors du glissement de la tête de lecture."""
    # Démarre le drag dans la règle
    qtbot.mousePress(timeline, Qt.MouseButton.LeftButton, pos=QPoint(100, 10))
    assert timeline._dragging_playhead

    # Mouvement vers 250px
    qtbot.mouseMove(timeline, pos=QPoint(250, 10))
    expected_seconds = timeline.seconds_for(250)
    assert timeline.position == pytest.approx(expected_seconds, rel=1e-3)

    # Relâchement
    qtbot.mouseRelease(timeline, Qt.MouseButton.LeftButton, pos=QPoint(250, 10))
    assert not timeline._dragging_playhead


# ---------------------------------------------------------------------------
# Tests : Rendu Graphique (paintEvent)
# ---------------------------------------------------------------------------

def test_paint_event_does_not_crash(timeline, sample_tracks, qtbot):
    """Vérifie que la timeline et tous ses types de clips (vidéo, audio, texte) se dessinent sans plantage."""
    timeline.show()
    qtbot.waitExposed(timeline)

    # Rendu initial
    timeline.repaint()

    # Rendu avec clip sélectionné (déclenche le contour vert de sélection)
    timeline.select(sample_tracks[0], sample_tracks[0]["clips"][0])
    timeline.repaint()

    # Rendu avec tête de lecture au milieu
    timeline.set_position(4.0)
    timeline.repaint()