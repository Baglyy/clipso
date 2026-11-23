"""Réglages d'un clip : un dataclass par onglet du panneau Propriétés."""

from dataclasses import dataclass


@dataclass
class TextStyle:
    font: str = "Nunito Black"
    size: int = 84  # en pixels pour une image de 1080 de haut
    color: str = "#FFFFFF"
    align: str = "center"
    animation: str = "fade"


@dataclass
class ImageSettings:
    # position du centre de l'image, en % de la largeur et de la hauteur
    x: int = 50
    y: int = 50
    scale: int = 100
    opacity: int = 100
    rotation: int = 0
    blend: str = "normal"


@dataclass
class Filters:
    preset: str = "original"
    brightness: int = 0
    contrast: int = 0
    saturation: int = 0
    temperature: int = 0

    @property
    def is_neutral(self) -> bool:
        return self == Filters()


@dataclass
class Blur:
    kind: str = "gaussian"
    intensity: int = 0
    feather: int = 30
    background: bool = False


@dataclass
class AudioSettings:
    volume: int = 100
    fade_in: float = 0.0  # en secondes
    fade_out: float = 0.0
    muted: bool = False
    normalize: bool = False
