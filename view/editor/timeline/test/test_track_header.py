import pytest
from PyQt6.QtCore import QSize, Qt
from PyQt6.QtWidgets import QLabel, QToolButton

# Adapter l'import selon l'arborescence de votre projet
from view.editor.timeline.track_header import TrackHeader


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def video_track_data():
    """Données d'une piste vidéo standard."""
    return {"name": "Piste Vidéo 1", "kind": "video"}


@pytest.fixture
def audio_track_data():
    """Données d'une piste audio standard."""
    return {"name": "Piste Audio 1", "kind": "audio"}


@pytest.fixture
def custom_icon_track_data():
    """Données d'une piste avec une icône explicite."""
    return {"name": "Sous-titres", "kind": "video", "icon": "text-align-left"}


@pytest.fixture
def video_header(qtbot, video_track_data):
    """Fixture créant un TrackHeader vidéo géré par qtbot."""
    header = TrackHeader(video_track_data, height=48)
    qtbot.addWidget(header)
    return header


@pytest.fixture
def audio_header(qtbot, audio_track_data):
    """Fixture créant un TrackHeader audio géré par qtbot."""
    header = TrackHeader(audio_track_data, height=36)
    qtbot.addWidget(header)
    return header


# ---------------------------------------------------------------------------
# Tests : Initialisation et Propriétés
# ---------------------------------------------------------------------------

def test_initial_properties(video_header, video_track_data):
    """Vérifie l'initialisation générale du widget (hauteur, objectName, layout, nom)."""
    assert video_header.objectName() == "trackHeader"
    assert video_header.height() == 48

    # Vérification des marges et espacements du layout
    layout = video_header.layout()
    assert layout is not None
    assert layout.contentsMargins().left() == 10
    assert layout.contentsMargins().right() == 6
    assert layout.spacing() == 6

    # Vérification du label affichant le nom de la piste
    name_label = video_header.findChild(QLabel, "trackName")
    assert name_label is not None
    assert name_label.text() == video_track_data["name"]


def test_custom_icon_used_when_provided(qtbot, custom_icon_track_data):
    """Vérifie que la création réussit sans erreur avec une icône personnalisée."""
    header = TrackHeader(custom_icon_track_data, height=40)
    qtbot.addWidget(header)
    assert header.findChild(QLabel, "trackName").text() == "Sous-titres"


# ---------------------------------------------------------------------------
# Tests : Boutons (Visibilité / Mute et Verrou)
# ---------------------------------------------------------------------------

def test_video_track_buttons_config(video_header):
    """Vérifie la configuration des boutons pour une piste vidéo."""
    vis_button = video_header.visibility_button
    lock_button = video_header.lock_button

    # Bouton de visibilité vidéo
    assert vis_button.objectName() == "trackButton"
    assert vis_button.isCheckable()
    assert not vis_button.isChecked()
    assert vis_button.toolTip() == "Masquer la piste"
    assert vis_button.size() == QSize(24, 24)
    assert vis_button.iconSize() == QSize(16, 16)
    assert not vis_button.icon().isNull()

    # Bouton de verrouillage
    assert lock_button.objectName() == "trackButton"
    assert lock_button.isCheckable()
    assert not lock_button.isChecked()
    assert lock_button.toolTip() == "Verrouiller la piste"
    assert lock_button.size() == QSize(24, 24)
    assert lock_button.iconSize() == QSize(16, 16)
    assert not lock_button.icon().isNull()


def test_audio_track_buttons_config(audio_header):
    """Vérifie que la piste audio adapte le tooltip du bouton de coupure du son."""
    vis_button = audio_header.visibility_button
    assert vis_button.toolTip() == "Couper la piste"


# ---------------------------------------------------------------------------
# Tests : Interactions et Changement d'icônes au clic
# ---------------------------------------------------------------------------

def test_visibility_button_toggle(video_header, qtbot):
    """Vérifie que le clic sur le bouton de visibilité bascule son état sans erreur."""
    button = video_header.visibility_button

    with qtbot.waitSignal(button.toggled, timeout=1000) as blocker:
        qtbot.mouseClick(button, Qt.MouseButton.LeftButton)

    assert button.isChecked()
    assert blocker.args == [True]
    assert not button.icon().isNull()

    # Second clic : rétablissement de l'état initial
    with qtbot.waitSignal(button.toggled, timeout=1000) as blocker:
        qtbot.mouseClick(button, Qt.MouseButton.LeftButton)

    assert not button.isChecked()
    assert blocker.args == [False]
    assert not button.icon().isNull()


def test_lock_button_toggle(video_header, qtbot):
    """Vérifie que le clic sur le bouton de verrouillage bascule son état sans erreur."""
    button = video_header.lock_button

    with qtbot.waitSignal(button.toggled, timeout=1000) as blocker:
        qtbot.mouseClick(button, Qt.MouseButton.LeftButton)

    assert button.isChecked()
    assert blocker.args == [True]
    assert not button.icon().isNull()

    # Déverrouillage
    with qtbot.waitSignal(button.toggled, timeout=1000) as blocker:
        qtbot.mouseClick(button, Qt.MouseButton.LeftButton)

    assert not button.isChecked()
    assert blocker.args == [False]
    assert not button.icon().isNull()


# ---------------------------------------------------------------------------
# Tests : Affichage & Rendu
# ---------------------------------------------------------------------------

def test_paint_event_does_not_crash(video_header, qtbot):
    """Vérifie que le header s'affiche et se repeint sans exception."""
    video_header.show()
    qtbot.waitExposed(video_header)
    video_header.repaint()