import os

import pytest

# pas de fenêtre à l'écran pendant les tests (marche aussi sans affichage, ex. en CI)
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

@pytest.fixture(autouse=True)
def _qapp(qapp):
    """Qt a besoin d'une QApplication pour créer des pixmaps, icônes et widgets."""
