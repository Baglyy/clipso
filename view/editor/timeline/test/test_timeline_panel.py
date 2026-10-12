import pytest
from PyQt6.QtCore import Qt

# Adapter l'import selon l'arborescence de votre projet
from view.editor.timeline.timeline_panel import ZOOM_STEP, TimelinePanel
from view.editor.timeline.timeline_view import RULER_HEIGHT, TRACK_HEIGHTS
from view.editor.timeline.track_header import TrackHeader


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_tracks():
    """Jeu de données de pistes pour la timeline."""
    return [
        {
            "name": "Piste Vidéo 1",
            "kind": "video",
            "clips": [
                {"name": "clip_intro.mp4", "kind": "video", "start": 0.0, "duration": 4.0, "color": "#3498DB"}
            ],
        },
        {
            "name": "Piste Audio 1",
            "kind": "audio",
            "clips": [
                {"name": "musique.mp3", "kind": "audio", "start": 0.0, "duration": 8.0}
            ],
        },
        {
            "name": "Titres",
            "kind": "overlay",
            "clips": [
                {"name": "Titre", "kind": "text", "start": 1.0, "duration": 2.0, "text": "Bonjour"}
            ],
        },
    ]


@pytest.fixture
def panel(qtbot):
    """Fixture créant une instance de TimelinePanel gérée par qtbot."""
    widget = TimelinePanel()
    qtbot.addWidget(widget)
    widget.resize(900, 400)
    return widget


# ---------------------------------------------------------------------------
# Tests : Initialisation
# ---------------------------------------------------------------------------

def test_initial_state(panel):
    """Vérifie l'état initial des composants du panneau."""
    assert panel.testAttribute(Qt.WidgetAttribute.WA_StyledBackground)
    assert panel.headers == []
    assert not panel.magnetButton.icon().isNull()
    assert not panel.selectionIcon.pixmap().isNull()


def test_magnet_button_toggle(panel, qtbot):
    """Vérifie que le basculement du bouton aimant met à jour l'icône sans erreur."""
    initial_checked = panel.magnetButton.isChecked()

    qtbot.mouseClick(panel.magnetButton, Qt.MouseButton.LeftButton)
    assert panel.magnetButton.isChecked() != initial_checked
    assert not panel.magnetButton.icon().isNull()

    # Rétablissement
    qtbot.mouseClick(panel.magnetButton, Qt.MouseButton.LeftButton)
    assert panel.magnetButton.isChecked() == initial_checked
    assert not panel.magnetButton.icon().isNull()


# ---------------------------------------------------------------------------
# Tests : Zoom
# ---------------------------------------------------------------------------

def test_zoom_slider_updates_timeline_view(panel):
    """Vérifie que modifier la valeur du slider ajuste le zoom de la timeline."""
    panel.zoomSlider.setValue(150)
    assert panel.timelineView.zoom == pytest.approx(1.5)

    panel.zoomSlider.setValue(200)
    assert panel.timelineView.zoom == pytest.approx(2.0)

    # Retour à 100% (minimum du slider)
    panel.zoomSlider.setValue(100)
    assert panel.timelineView.zoom == pytest.approx(1.0)

def test_zoom_in_button(panel, qtbot):
    """Vérifie que le bouton zoom avant incrémente le slider du ZOOM_STEP."""
    panel.zoomSlider.setValue(100)
    qtbot.mouseClick(panel.zoomInButton, Qt.MouseButton.LeftButton)
    assert panel.zoomSlider.value() == 100 + ZOOM_STEP


def test_zoom_out_button(panel, qtbot):
    """Vérifie que le bouton zoom arrière décrémente le slider du ZOOM_STEP."""
    panel.zoomSlider.setValue(150)
    qtbot.mouseClick(panel.zoomOutButton, Qt.MouseButton.LeftButton)
    assert panel.zoomSlider.value() == 150 - ZOOM_STEP


def test_fit_timeline_button(panel, qtbot):
    """Vérifie que le bouton d'ajustement réinitialise le zoom à 100%."""
    panel.zoomSlider.setValue(250)
    qtbot.mouseClick(panel.fitTimelineButton, Qt.MouseButton.LeftButton)
    assert panel.zoomSlider.value() == 100
    assert panel.timelineView.zoom == pytest.approx(1.0)


# ---------------------------------------------------------------------------
# Tests : Défilement & Synchronisation ScrollBar
# ---------------------------------------------------------------------------

def test_scrollbar_update_on_overflow(panel):
    """Vérifie l'activation et les bornes de la barre de défilement selon le dépassement."""
    view_width = panel.timelineView.width()

    # Cas avec débordement (contenu plus large que la vue)
    content_width = view_width + 400
    panel._update_scrollbar(content_width)

    assert panel.timelineScrollBar.isEnabled()
    assert panel.timelineScrollBar.maximum() == 400
    assert panel.timelineScrollBar.pageStep() == view_width

    # Cas sans débordement
    panel._update_scrollbar(view_width - 50)
    assert not panel.timelineScrollBar.isEnabled()
    assert panel.timelineScrollBar.maximum() == 0


def test_scrollbar_scrolls_timeline_offset(panel):
    """Vérifie que le défilement de la scrollbar modifie l'offset de la TimelineView."""
    panel.timelineScrollBar.setMaximum(200)
    panel.timelineScrollBar.setValue(85)
    assert panel.timelineView.offset == 85


# ---------------------------------------------------------------------------
# Tests : En-têtes de pistes (set_tracks) et Sélection
# ---------------------------------------------------------------------------

def test_set_tracks_creates_headers(panel, sample_tracks):
    """Vérifie la création des TrackHeader et la transmission des données à la timeline."""
    panel.set_tracks(sample_tracks, duration=10.0)

    assert len(panel.headers) == len(sample_tracks)
    assert all(isinstance(header, TrackHeader) for header in panel.headers)

    # Vérifie que la hauteur de chaque header correspond à TRACK_HEIGHTS
    for header, track in zip(panel.headers, sample_tracks):
        assert header.height() == TRACK_HEIGHTS[track["kind"]]

    assert panel.addTrackButton.height() == RULER_HEIGHT
    assert panel.timelineView.tracks == sample_tracks
    assert panel.timelineView.duration == 10.0


def test_set_tracks_replaces_previous_headers(panel, sample_tracks):
    """Vérifie qu'un nouvel appel à set_tracks remplace les anciens en-têtes sans duplicat."""
    panel.set_tracks(sample_tracks, duration=10.0)
    old_headers = list(panel.headers)

    new_tracks = [{"name": "Seule Piste", "kind": "audio", "clips": []}]
    panel.set_tracks(new_tracks, duration=5.0)

    assert len(panel.headers) == 1
    assert panel.headers[0] not in old_headers
    assert panel.timelineView.duration == 5.0


def test_clip_selected_updates_selection_label(panel, sample_tracks):
    """Vérifie que la sélection d'un clip met à jour le texte du label d'information."""
    panel.set_tracks(sample_tracks, duration=10.0)

    selected_clip = sample_tracks[0]["clips"][0]
    panel.timelineView.clip_selected.emit(sample_tracks[0], selected_clip)

    assert panel.timelineSelectionLabel.text() == selected_clip["name"]


# ---------------------------------------------------------------------------
# Tests : Rendu Graphique
# ---------------------------------------------------------------------------

def test_paint_event_does_not_crash(panel, sample_tracks, qtbot):
    """Vérifie que le panneau complet s'affiche et se repeint sans exception."""
    panel.set_tracks(sample_tracks, duration=10.0)
    panel.show()
    qtbot.waitExposed(panel)

    panel.repaint()