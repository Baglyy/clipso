import pytest
from PyQt6.QtCore import Qt

# Adapter l'import selon l'arborescence de votre projet
from view.editor.media.media_panel import COLUMNS, MediaPanel
from view.editor.media.media_tile import MediaTile

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_media():
    """Jeu de données de test contenant plusieurs types de médias."""
    return [
        {"name": "clip_1.mp4", "kind": "video", "color": "#3498DB", "duration": "00:10"},
        {"name": "voiceover.wav", "kind": "audio", "duration": "01:20"},
        {"name": "photo_1.png", "kind": "image", "color": "#E74C3C"},
        {"name": "clip_2.mov", "kind": "video", "color": "#2ECC71", "duration": "00:45"},
    ]


@pytest.fixture
def panel(qtbot):
    """Fixture créant une instance de MediaPanel gérée par qtbot."""
    widget = MediaPanel()
    qtbot.addWidget(widget)
    return widget


# ---------------------------------------------------------------------------
# Tests : Initialisation
# ---------------------------------------------------------------------------


def test_initial_state(panel):
    """Vérifie l'état initial du panneau (liste vide, dictionnaire de filtres)."""
    assert panel.tiles == []
    assert panel._stretch_row == 0
    # Correction : testAttribute au lieu de attribute
    assert panel.testAttribute(Qt.WidgetAttribute.WA_StyledBackground)

    # Vérification que tous les boutons de filtres sont mappés
    expected_filters = {
        panel.filterAllButton: None,
        panel.filterVideoButton: "video",
        panel.filterAudioButton: "audio",
        panel.filterImageButton: "image",
    }
    assert panel._filters == expected_filters


# ---------------------------------------------------------------------------
# Tests : Alimentation des médias (set_media)
# ---------------------------------------------------------------------------


def test_set_media_populates_tiles_and_label(panel, sample_media):
    """Vérifie l'ajout de médias : création des tiles, label de compteur et disposition."""
    panel.set_media(sample_media)

    assert len(panel.tiles) == len(sample_media)
    assert panel.mediaCountLabel.text() == f"{len(sample_media)} fichiers"
    assert all(isinstance(tile, MediaTile) for tile in panel.tiles)

    # Correction : not isHidden() au lieu de isVisible() (car le panel n'est pas encore show())
    visible_tiles = [tile for tile in panel.tiles if not tile.isHidden()]
    assert len(visible_tiles) == len(sample_media)

    # Vérifie le placement dans la grille (index // COLUMNS, index % COLUMNS)
    grid = panel.mediaGrid
    for index, tile in enumerate(visible_tiles):
        row, col, _, _ = grid.getItemPosition(grid.indexOf(tile))
        assert row == index // COLUMNS
        assert col == index % COLUMNS


def test_set_media_replaces_existing_tiles(panel, sample_media):
    """Vérifie qu'un nouvel appel à set_media remplace correctement les anciennes vignettes."""
    panel.set_media(sample_media)
    old_tiles = list(panel.tiles)

    new_media = [{"name": "nouveau.mp4", "kind": "video", "color": "#9B59B6"}]
    panel.set_media(new_media)

    assert len(panel.tiles) == 1
    assert panel.tiles[0] not in old_tiles
    assert panel.mediaCountLabel.text() == "1 fichiers"


# ---------------------------------------------------------------------------
# Tests : Filtrage
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("filter_button_attr", "expected_kind", "expected_count"),
    [
        ("filterVideoButton", "video", 2),
        ("filterAudioButton", "audio", 1),
        ("filterImageButton", "image", 1),
    ],
)
def test_filtering_by_type(panel, sample_media, filter_button_attr, expected_kind, expected_count):
    """Vérifie que l'activation d'un filtre n'affiche que les médias correspondants."""
    panel.set_media(sample_media)

    button = getattr(panel, filter_button_attr)
    button.setChecked(True)

    visible_tiles = [tile for tile in panel.tiles if not tile.isHidden()]
    hidden_tiles = [tile for tile in panel.tiles if tile.isHidden()]

    assert len(visible_tiles) == expected_count
    assert all(tile.media["kind"] == expected_kind for tile in visible_tiles)
    assert len(hidden_tiles) == len(sample_media) - expected_count


def test_filter_all_restores_all_tiles(panel, sample_media):
    """Vérifie que la sélection du filtre 'Tous' réaffiche l'intégralité des éléments."""
    panel.set_media(sample_media)

    # Active d'abord le filtre vidéo
    panel.filterVideoButton.setChecked(True)
    assert len([tile for tile in panel.tiles if not tile.isHidden()]) == 2

    # Réactive le filtre global
    panel.filterAllButton.setChecked(True)
    visible_tiles = [tile for tile in panel.tiles if not tile.isHidden()]
    assert len(visible_tiles) == len(sample_media)


def test_stretch_row_updated_on_filter(panel, sample_media):
    """Vérifie que la ligne de stretch absorbant l'espace restant est mise à jour."""
    panel.set_media(sample_media)  # 4 éléments -> 4 // 2 + 1 = 3
    assert panel._stretch_row == (len(sample_media) // COLUMNS) + 1

    # Filtre audio : 1 élément -> 1 // 2 + 1 = 1
    panel.filterAudioButton.setChecked(True)
    assert panel._stretch_row == 1


# ---------------------------------------------------------------------------
# Tests : Affichage & Rendu
# ---------------------------------------------------------------------------


def test_paint_event_does_not_crash(panel, sample_media, qtbot):
    """Vérifie que le panneau et ses composants graphiques se rendent sans exception."""
    panel.set_media(sample_media)
    panel.show()
    qtbot.waitExposed(panel)

    panel.repaint()
