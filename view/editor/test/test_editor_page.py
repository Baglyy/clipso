import pytest
from PyQt6.QtCore import Qt

from view.editor.editor_page import EditorPage
from view.editor.preview.preview_panel import FPS

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def project_data():
    """Données d'un projet de test complet."""
    video_clip = {
        "name": "intro.mp4",
        "kind": "video",
        "start": 0.0,
        "duration": 5.0,
        "color": "#3498DB",
    }
    image_clip = {
        "name": "logo.png",
        "kind": "image",
        "start": 2.0,
        "duration": 3.0,
    }
    text_clip = {
        "name": "Titre",
        "kind": "text",
        "start": 1.0,
        "duration": 2.0,
        "text": "Mon Titre",
    }

    return {
        "name": "Projet Démo",
        "duration": 10.0,
        "position": 2.0,
        "media": [
            {"name": "intro.mp4", "kind": "video", "color": "#3498DB", "duration": "00:05"},
            {"name": "logo.png", "kind": "image", "color": "#E74C3C"},
        ],
        "tracks": [
            {"name": "Piste Vidéo", "kind": "video", "clips": [video_clip]},
            {"name": "Piste Image", "kind": "overlay", "clips": [image_clip]},
            {"name": "Piste Titre", "kind": "overlay", "clips": [text_clip]},
        ],
    }


@pytest.fixture
def page(qtbot):
    """Fixture créant une instance de EditorPage gérée par qtbot avec arrêt garanti du timer."""
    widget = EditorPage()
    qtbot.addWidget(widget)
    widget.resize(1280, 720)
    yield widget
    # Empêche tout Segfault : neutralise le timer avant le garbage collection
    widget.playback_timer.stop()


@pytest.fixture
def loaded_page(page, project_data):
    """Fixture avec un projet déjà chargé dans EditorPage."""
    page.load_project(
        name=project_data["name"],
        media=project_data["media"],
        tracks=project_data["tracks"],
        duration=project_data["duration"],
        position=project_data["position"],
    )
    return page


# ---------------------------------------------------------------------------
# Tests : Initialisation & Propriétés
# ---------------------------------------------------------------------------

def test_initial_state(page):
    """Vérifie l'état initial des splitters, menus et timers de la page."""
    assert page.testAttribute(Qt.WidgetAttribute.WA_StyledBackground)
    assert page.duration == 0.0
    assert not page.playback_timer.isActive()
    assert page.playback_timer.interval() == 1000 // FPS

    assert page.fileMenuButton.menu() is not None
    assert page.editMenuButton.menu() is not None
    assert page.viewMenuButton.menu() is not None


# ---------------------------------------------------------------------------
# Tests : Chargement de Projet (load_project)
# ---------------------------------------------------------------------------

def test_load_project(loaded_page, project_data):
    """Vérifie l'initialisation du titre, de la durée, des panneaux et de la position."""
    assert loaded_page.duration == project_data["duration"]
    assert loaded_page.projectNameLabel.text() == project_data["name"]
    assert len(loaded_page.mediaPanel.tiles) == len(project_data["media"])
    assert len(loaded_page.timeline.tracks) == len(project_data["tracks"])
    assert loaded_page.timeline.position == pytest.approx(project_data["position"])


# ---------------------------------------------------------------------------
# Tests : Signaux de la Barre Supérieure et Menus
# ---------------------------------------------------------------------------

def test_logo_button_emits_home_requested(page, qtbot):
    """Vérifie que le clic sur le logo émet home_requested."""
    with qtbot.waitSignal(page.home_requested, timeout=1000):
        qtbot.mouseClick(page.logoButton, Qt.MouseButton.LeftButton)


def test_export_button_emits_export_requested(page, qtbot):
    """Vérifie que le clic sur le bouton exporter émet export_requested."""
    with qtbot.waitSignal(page.export_requested, timeout=1000):
        qtbot.mouseClick(page.exportButton, Qt.MouseButton.LeftButton)


def test_menu_actions_emit_signals(page, qtbot):
    """Vérifie le déclenchement des actions Exporter et Accueil depuis le menu Fichier."""
    file_menu = page.fileMenuButton.menu()
    actions = {action.text(): action for action in file_menu.actions() if not action.isSeparator()}

    with qtbot.waitSignal(page.export_requested, timeout=1000):
        actions["Exporter…"].trigger()

    with qtbot.waitSignal(page.home_requested, timeout=1000):
        actions["Retour à l'accueil"].trigger()


def test_view_menu_zoom_actions(page):
    """Vérifie que les actions du menu Affichage déclenchent les contrôles de zoom."""
    view_menu = page.viewMenuButton.menu()
    actions = {action.text(): action for action in view_menu.actions()}

    initial_zoom = page.timelinePanel.zoomSlider.value()

    actions["Zoom avant"].trigger()
    assert page.timelinePanel.zoomSlider.value() > initial_zoom

    actions["Ajuster la timeline"].trigger()
    assert page.timelinePanel.zoomSlider.value() == 100


# ---------------------------------------------------------------------------
# Tests : Navigation Temporelle (seek, jump, step)
# ---------------------------------------------------------------------------

def test_seek_updates_timeline_and_preview(loaded_page):
    """Vérifie que seek met à jour la position de la timeline."""
    loaded_page.seek(4.5)
    assert loaded_page.timeline.position == pytest.approx(4.5)
    # Vérifie que le label a bien été mis à jour sans figer le format exact
    assert len(loaded_page.previewPanel.timecodeLabel.text()) > 0


def test_preview_step_requested(loaded_page):
    """Vérifie l'incrément de pas temporel émis par le previewPanel."""
    loaded_page.seek(3.0)
    loaded_page.previewPanel.step_requested.emit(1.5)
    assert loaded_page.timeline.position == pytest.approx(4.5)


def test_preview_jump_requested(loaded_page):
    """Vérifie les sauts au début et à la fin émis par le previewPanel."""
    loaded_page.previewPanel.jump_requested.emit("start")
    assert loaded_page.timeline.position == 0.0

    loaded_page.previewPanel.jump_requested.emit("end")
    assert loaded_page.timeline.position == pytest.approx(loaded_page.duration)


# ---------------------------------------------------------------------------
# Tests : Lecture et Timer (Playback)
# ---------------------------------------------------------------------------

def test_playback_start_and_stop(loaded_page):
    """Vérifie le démarrage et l'arrêt du timer de lecture."""
    loaded_page._set_playing(True)
    assert loaded_page.playback_timer.isActive()

    loaded_page._set_playing(False)
    assert not loaded_page.playback_timer.isActive()


def test_playback_starts_from_beginning_if_at_end(loaded_page):
    """Vérifie que lancer la lecture en fin de timeline redémarre à 0."""
    try:
        loaded_page.seek(loaded_page.duration)
        loaded_page._set_playing(True)

        assert loaded_page.timeline.position == 0.0
        assert loaded_page.playback_timer.isActive()
    finally:
        loaded_page._set_playing(False)  # Arrêt garanti


def test_playback_timer_tick_advances_playhead(loaded_page):
    """Vérifie qu'un tick de timer avance la tête de lecture d'une frame (1 / FPS)."""
    loaded_page.seek(1.0)
    loaded_page.playback_timer.timeout.emit()

    assert loaded_page.timeline.position == pytest.approx(1.0 + 1 / FPS, rel=1e-3)


def test_playback_stops_automatically_at_duration(loaded_page):
    """Vérifie que la lecture s'interrompt quand la fin du projet est atteinte."""
    try:
        loaded_page.previewPanel.set_playing(True)
        loaded_page._set_playing(True)

        loaded_page.seek(loaded_page.duration)

        assert not loaded_page.playback_timer.isActive()
        assert not loaded_page.previewPanel.playing
    finally:
        loaded_page._set_playing(False)


# ---------------------------------------------------------------------------
# Tests : Sélection de Clips
# ---------------------------------------------------------------------------

def test_select_clip(loaded_page, project_data):
    """Vérifie la sélection d'un clip dans la timeline."""
    target_clip = project_data["tracks"][0]["clips"][0]

    loaded_page.select_clip(target_clip)
    assert loaded_page.timeline.selected is target_clip


# ---------------------------------------------------------------------------
# Tests : Rendu Graphique
# ---------------------------------------------------------------------------

def test_paint_event_does_not_crash(loaded_page, qtbot):
    """Vérifie que la page s'affiche et planifie son rafraîchissement sans crash."""
    loaded_page.show()
    qtbot.waitExposed(loaded_page)
    # update() au lieu de repaint() pour respecter le pipeline OpenGL de previewPanel
    loaded_page.update()
