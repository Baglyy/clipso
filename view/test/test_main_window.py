import pytest
from PyQt6.QtCore import QSize, Qt

from view.dialogs.export_dialog import ExportDialog
from view.main_window import MainWindow


# ---------------------------------------------------------------------------
# Fixture
# ---------------------------------------------------------------------------

@pytest.fixture
def window(qtbot):
    """Fixture créant une instance de MainWindow gérée par qtbot."""
    win = MainWindow()
    qtbot.addWidget(win)
    return win


# ---------------------------------------------------------------------------
# Tests : État initial et Configuration
# ---------------------------------------------------------------------------

def test_initial_window_properties(window):
    """Vérifie le titre, les dimensions et la configuration de la fenêtre principale."""
    assert window.windowTitle() == "Clipso"
    assert window.minimumSize() == QSize(1100, 700)
    assert window.size() == QSize(1440, 860)


def test_initial_pages_setup(window):
    """Vérifie que le QStackedWidget contient les deux pages et affiche l'accueil par défaut."""
    assert window.pages is window.centralWidget()
    assert window.pages.count() == 2
    assert window.pages.indexOf(window.home_page) == 0
    assert window.pages.indexOf(window.editor_page) == 1

    # La page active par défaut doit être la page d'accueil
    assert window.pages.currentWidget() is window.home_page


def test_demo_project_loaded_in_editor(window):
    """Vérifie que le projet démo est chargé dans l'éditeur dès l'initialisation."""
    assert window.editor_page.projectNameLabel.text() == "Vacances à Biarritz"
    assert len(window.editor_page.timeline.tracks) > 0
    assert window.editor_page.timeline.selected is not None


# ---------------------------------------------------------------------------
# Tests : Navigation entre Pages
# ---------------------------------------------------------------------------

def test_show_editor_and_show_home_methods(window):
    """Vérifie le basculement direct entre les pages via les méthodes dédiées."""
    window.show_editor()
    assert window.pages.currentWidget() is window.editor_page

    window.show_home()
    assert window.pages.currentWidget() is window.home_page


def test_create_and_open_buttons_navigate_to_editor(window, qtbot):
    """Vérifie que les boutons 'Créer' et 'Ouvrir' de l'accueil basculent vers l'éditeur."""
    # Clic sur le bouton Créer
    qtbot.mouseClick(window.home_page.createProjectButton, Qt.MouseButton.LeftButton)
    assert window.pages.currentWidget() is window.editor_page

    # Retour à l'accueil
    window.show_home()

    # Clic sur le bouton Ouvrir
    qtbot.mouseClick(window.home_page.openProjectButton, Qt.MouseButton.LeftButton)
    assert window.pages.currentWidget() is window.editor_page


def test_editor_home_requested_navigates_to_home(window):
    """Vérifie que le signal home_requested de l'éditeur renvoie vers l'accueil."""
    window.show_editor()
    assert window.pages.currentWidget() is window.editor_page

    # Émission du signal de retour à l'accueil
    window.editor_page.home_requested.emit()
    assert window.pages.currentWidget() is window.home_page


def test_recent_project_item_navigates_to_editor(window):
    """Vérifie que cliquer / ouvrir un projet récent bascule vers l'éditeur."""
    window.show_home()

    # Récupère le premier projet récent et simule sa demande d'ouverture
    recent_items = window.home_page.findChildren(object, name="recentProjectItem")
    if recent_items:
        recent_items[0].open_requested.emit()
        assert window.pages.currentWidget() is window.editor_page


# ---------------------------------------------------------------------------
# Tests : Boîte de dialogue d'Export
# ---------------------------------------------------------------------------

def test_show_export_executes_dialog(window, monkeypatch):
    """Vérifie que la demande d'export exécute bien ExportDialog (dialogue bloqué neutralisé)."""
    dialog_executed = False

    def fake_exec(self):
        nonlocal dialog_executed
        dialog_executed = True
        return 1

    # Neutralise l'appel bloquant .exec() pour le test
    monkeypatch.setattr(ExportDialog, "exec", fake_exec)

    window.editor_page.export_requested.emit()
    assert dialog_executed


# ---------------------------------------------------------------------------
# Tests : Affichage & Rendu
# ---------------------------------------------------------------------------

def test_window_paint_and_display(window, qtbot):
    """Vérifie que la fenêtre complète s'affiche et se repeint sans exception."""
    window.show()
    qtbot.waitExposed(window)

    window.repaint()

    # Teste également le rendu de la page éditeur
    window.show_editor()
    window.repaint()