import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


@pytest.fixture(scope="session")
def app():
    from PyQt6.QtWidgets import QApplication

    from main import load_style

    application = QApplication.instance() or QApplication([])
    load_style(application)
    return application


@pytest.fixture
def window(app):
    from view.main_window import MainWindow

    main_window = MainWindow()
    main_window.show()
    yield main_window
    main_window.close()


@pytest.fixture
def editor(window):
    window.show_editor()
    return window.editor_page
