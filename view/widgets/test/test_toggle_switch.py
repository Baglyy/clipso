import pytest
from PyQt6.QtCore import QPoint, QSize, Qt

from view.widgets.toggle_switch import ToggleSwitch


@pytest.fixture
def toggle(qtbot):
    """Fixture créant une instance de ToggleSwitch gérée par qtbot."""
    widget = ToggleSwitch()
    qtbot.addWidget(widget)
    return widget


def test_initial_state(toggle):
    """Vérifie l'état initial du switch."""
    assert not toggle.isChecked()
    assert toggle.size() == QSize(40, 22)
    assert toggle.sizeHint() == QSize(40, 22)
    assert toggle.cursor().shape() == Qt.CursorShape.PointingHandCursor


def test_toggle_state_programmatically(toggle):
    """Vérifie le changement d'état via setChecked()."""
    toggle.setChecked(True)
    assert toggle.isChecked()

    toggle.setChecked(False)
    assert not toggle.isChecked()


def test_mouse_click_toggles_state_and_emits_signal(toggle, qtbot):
    """Vérifie qu'un clic de souris inverse l'état et émet le signal toggled."""
    # Surveillance du signal 'toggled'
    with qtbot.waitSignal(toggle.toggled, timeout=1000) as blocker:
        qtbot.mouseClick(toggle, Qt.MouseButton.LeftButton)

    assert toggle.isChecked()
    assert blocker.args == [True]

    # Deuxième clic pour éteindre
    with qtbot.waitSignal(toggle.toggled, timeout=1000) as blocker:
        qtbot.mouseClick(toggle, Qt.MouseButton.LeftButton)

    assert not toggle.isChecked()
    assert blocker.args == [False]


def test_hit_button(toggle):
    """Vérifie la zone de clic personnalisée (hitButton)."""
    # Points à l'intérieur du widget (40x22)
    assert toggle.hitButton(QPoint(0, 0))
    assert toggle.hitButton(QPoint(20, 11))
    assert toggle.hitButton(QPoint(39, 21))

    # Points en dehors du widget
    assert not toggle.hitButton(QPoint(-1, 0))
    assert not toggle.hitButton(QPoint(40, 10))
    assert not toggle.hitButton(QPoint(10, 25))


def test_paint_event_does_not_crash(toggle, qtbot):
    """Vérifie que le paintEvent s'exécute sans exception (états False et True)."""
    toggle.show()
    qtbot.waitExposed(toggle)

    # Force le rendu à l'état désactivé
    toggle.repaint()

    # Force le rendu à l'état activé
    toggle.setChecked(True)
    toggle.repaint()
