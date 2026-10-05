from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QLabel, QPushButton, QSlider

from view.format import percent
from view.ui_helpers import bind_value_label, clickable, setup_button


def test_clickable_sets_hand_cursor():
    a, b = QPushButton(), QLabel()
    clickable(a, b)
    assert a.cursor().shape() == Qt.CursorShape.PointingHandCursor
    assert b.cursor().shape() == Qt.CursorShape.PointingHandCursor


def test_setup_button():
    button = QPushButton()
    setup_button(button, "play", size=24)
    assert not button.icon().isNull()
    assert button.iconSize().width() == 24
    assert button.cursor().shape() == Qt.CursorShape.PointingHandCursor


def test_bind_value_label_updates_text():
    slider, label = QSlider(), QLabel()
    bind_value_label(slider, label, percent)
    slider.setValue(30)
    assert label.text() == "30 %"
    assert slider.cursor().shape() == Qt.CursorShape.PointingHandCursor
