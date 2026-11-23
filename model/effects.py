"""Effets appliqués à chaque image (tableau NumPy RGB) à l'export."""

import cv2
import numpy as np
from moviepy import vfx

from model.settings import Blur, Filters

PRESETS = {
    "original": Filters(),
    "warm": Filters(brightness=3, saturation=10, temperature=40),
    "cool": Filters(saturation=-5, temperature=-40),
    "mono": Filters(contrast=10, saturation=-100),
    "vintage": Filters(brightness=8, contrast=-20, saturation=-40, temperature=35),
    "pastel": Filters(brightness=20, contrast=-25, saturation=-30),
}
TEMPERATURE_STRENGTH = 0.4
MAX_BLUR = 0.03
MAX_MOTION = 0.12
MAX_ZOOM = 0.25
RADIAL_STEPS = 12
ANIMATION_DURATION = 0.5


def apply_filters(frame: np.ndarray, filters: Filters) -> np.ndarray:
    frame = _adjust(frame.astype(np.uint8), PRESETS[filters.preset])
    return _adjust(frame, filters)


def _adjust(frame: np.ndarray, filters: Filters) -> np.ndarray:
    if filters.brightness or filters.contrast or filters.temperature:
        values = np.arange(256)
        values = (values - 128) * (1 + filters.contrast / 100) + 128 + filters.brightness
        shift = filters.temperature * TEMPERATURE_STRENGTH
        table = np.stack([values + shift, values, values - shift], axis=1)
        table = np.clip(table, 0, 255).astype(np.uint8)
        frame = cv2.LUT(frame, table.reshape(1, 256, 3))
    if filters.saturation:
        gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
        gray = cv2.cvtColor(gray, cv2.COLOR_GRAY2RGB)
        amount = 1 + filters.saturation / 100
        frame = cv2.addWeighted(frame, amount, gray, 1 - amount, 0)
    return frame


def apply_blur(frame: np.ndarray, blur: Blur) -> np.ndarray:
    if blur.intensity == 0:
        return frame
    frame = frame.astype(np.uint8)
    strength = blur.intensity / 100
    if blur.kind == "motion":
        blurred = _motion_blur(frame, strength)
    elif blur.kind == "radial":
        blurred = _radial_blur(frame, strength)
    else:
        blurred = _gaussian_blur(frame, strength)
    if not blur.background:
        return blurred
    mask = _background_mask(frame.shape[0], frame.shape[1], blur.feather)
    return cv2.blendLinear(frame, blurred, 1 - mask, mask)


def _gaussian_blur(frame: np.ndarray, strength: float) -> np.ndarray:
    sigma = max(0.1, min(frame.shape[:2]) * MAX_BLUR * strength)
    if sigma < 8:
        return cv2.GaussianBlur(frame, (0, 0), sigma)
    # plus rapide sur une petite image
    height, width = frame.shape[:2]
    small = cv2.resize(frame, (width // 4, height // 4), interpolation=cv2.INTER_AREA)
    small = cv2.GaussianBlur(small, (0, 0), sigma / 4)
    return cv2.resize(small, (width, height), interpolation=cv2.INTER_LINEAR)


def _motion_blur(frame: np.ndarray, strength: float) -> np.ndarray:
    length = max(2, round(min(frame.shape[:2]) * MAX_MOTION * strength))
    return cv2.blur(frame, (length, 1))


def _radial_blur(frame: np.ndarray, strength: float) -> np.ndarray:
    height, width = frame.shape[:2]
    total = np.zeros(frame.shape, np.float32)
    for i in range(RADIAL_STEPS):
        zoom = 1 + MAX_ZOOM * strength * i / (RADIAL_STEPS - 1)
        matrix = cv2.getRotationMatrix2D((width / 2, height / 2), 0, zoom)
        total += cv2.warpAffine(frame, matrix, (width, height), borderMode=cv2.BORDER_REPLICATE)
    return np.clip(total / RADIAL_STEPS, 0, 255).astype(np.uint8)


def _background_mask(height: int, width: int, feather: int) -> np.ndarray:
    # 0 = net, 1 = flou
    y, x = np.ogrid[:height, :width]
    distance = np.sqrt(((x - width / 2) / (width * 0.3)) ** 2 + ((y - height / 2) / (height * 0.4)) ** 2)
    transition = max(feather / 100, 0.01)
    return np.clip((distance - 1) / transition, 0, 1).astype(np.float32)


def animate_text(layer, animation: str):
    duration = min(ANIMATION_DURATION, layer.duration)
    x, y = layer.pos(0)
    width, height = layer.size

    if animation == "fade":
        return layer.with_effects([vfx.CrossFadeIn(duration)])

    if animation == "slide":

        def position(t):
            progress = min(t / duration, 1)
            return -width + (x + width) * progress, y

        return layer.with_position(position)

    if animation == "zoom":

        def scale(t):
            return 0.1 + 0.9 * min(t / duration, 1)

        def centered(t):
            return x + width * (1 - scale(t)) / 2, y + height * (1 - scale(t)) / 2

        return layer.resized(scale).with_position(centered)

    return layer
