import os

import pytest

# pas de fenêtre à l'écran pendant les tests (marche aussi sans affichage, ex. en CI)
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QApplication  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def qapp():
    """Qt a besoin d'une QApplication pour créer des pixmaps, icônes et widgets."""
    app = QApplication.instance() or QApplication([])
    yield app
