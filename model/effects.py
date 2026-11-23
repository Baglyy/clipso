"""Effets appliqués à chaque image (tableau NumPy RGB) à l'export."""

import numpy as np

from model.settings import Blur, Filters


def apply_filters(frame: np.ndarray, filters: Filters) -> np.ndarray:
    # TODO: issue « Filtres » : appliquer filters.preset puis luminosité, contraste, saturation, température
    return frame


def apply_blur(frame: np.ndarray, blur: Blur) -> np.ndarray:
    # TODO: issue « Flou » : flou gaussien / mouvement / radial selon blur.kind, avec blur.feather et blur.background
    return frame


def animate_text(layer, animation: str):
    # TODO: issue « Animations de texte » : vfx.CrossFadeIn ("fade"), vfx.SlideIn ("slide"), zoom ("zoom")
    return layer
