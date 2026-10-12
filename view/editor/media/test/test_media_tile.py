import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QLabel, QSizePolicy

from view.editor.media.media_tile import MediaThumbnail, MediaTile


@pytest.fixture
def video_media():
    """Dictionnaire de média vidéo complet."""
    return {
        "name": "clip_intro.mp4",
        "kind": "video",
        "color": "#4A90E2",
        "duration": "01:23",
        "used": True,
    }


@pytest.fixture
def audio_media():
    """Dictionnaire de média audio complet."""
    return {
        "name": "voiceover.wav",
        "kind": "audio",
        "duration": "00:45",
        "used": False,
    }


@pytest.fixture
def minimal_media():
    """Dictionnaire minimal sans durée ni indicateur used."""
    return {
        "name": "photo.png",
        "kind": "image",
        "color": "#E94E77",
    }


@pytest.fixture
def media_thumbnail(qtbot, video_media):
    """Fixture créant une instance de MediaThumbnail gérée par qtbot."""
    widget = MediaThumbnail(video_media)
    qtbot.addWidget(widget)
    return widget


@pytest.fixture
def media_tile(qtbot, video_media):
    """Fixture créant une instance de MediaTile gérée par qtbot."""
    tile = MediaTile(video_media)
    qtbot.addWidget(tile)
    return tile



def test_thumbnail_initial_properties(media_thumbnail, video_media):
    """Vérifie la configuration initiale de la miniature (hauteur, policy, données)."""
    assert media_thumbnail.media == video_media
    assert media_thumbnail.height() == 66
    assert media_thumbnail.sizePolicy().verticalPolicy() == QSizePolicy.Policy.Fixed
    assert media_thumbnail.sizePolicy().horizontalPolicy() == QSizePolicy.Policy.Expanding


@pytest.mark.parametrize(
    "media_data",
    [
        # Audio avec durée et non utilisé
        {"name": "theme.mp3", "kind": "audio", "duration": "03:12", "used": False},
        # Vidéo avec durée et marquée comme utilisée
        {"name": "scenedeux.mov", "kind": "video", "color": "#2ECC71", "duration": "00:15", "used": True},
        # Média minimaliste sans options facultatives
        {"name": "logo.svg", "kind": "image", "color": "#F39C12"},
    ],
)
def test_thumbnail_paint_event_does_not_crash(qtbot, media_data):
    """Vérifie que le rendu de paintEvent s'exécute sans erreur selon le type de média."""
    widget = MediaThumbnail(media_data)
    qtbot.addWidget(widget)
    widget.resize(120, 66)

    widget.show()
    qtbot.waitExposed(widget)
    widget.repaint()

def test_tile_initial_properties(media_tile, video_media):
    """Vérifie l'état et les propriétés générales du tile."""
    assert media_tile.media == video_media
    assert media_tile.objectName() == "mediaTile"
    assert media_tile.toolTip() == video_media["name"]
    assert media_tile.cursor().shape() == Qt.CursorShape.PointingHandCursor


def test_tile_layout_and_child_widgets(media_tile, video_media):
    """Vérifie que la vignette et le label de titre sont bien instanciés et ajoutés au layout."""
    layout = media_tile.layout()
    assert layout is not None
    assert layout.contentsMargins().left() == 0
    assert layout.contentsMargins().top() == 0
    assert layout.spacing() == 5

    # Vérification de la présence de la miniature
    thumbnail = media_tile.findChild(MediaThumbnail)
    assert thumbnail is not None
    assert thumbnail.media == video_media

    # Vérification du label de nom
    name_label = media_tile.findChild(QLabel, "mediaName")
    assert name_label is not None
    assert name_label.text() == video_media["name"]


def test_tile_render_does_not_crash(media_tile, qtbot):
    """Vérifie que l'ensemble du MediaTile s'affiche et se repeint sans exception."""
    media_tile.show()
    qtbot.waitExposed(media_tile)
    media_tile.repaint()