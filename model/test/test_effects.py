import cv2
import numpy as np
import pytest
from moviepy import ColorClip

from model.effects import MAX_BLUR, PRESETS, animate_text, apply_blur, apply_filters
from model.settings import Blur, Filters


@pytest.fixture
def frame():
    rng = np.random.default_rng(1)
    return rng.integers(60, 190, (90, 160, 3), dtype=np.uint8)


@pytest.fixture
def square():
    image = np.zeros((90, 160, 3), dtype=np.uint8)
    image[30:60, 60:100] = 255
    return image


def test_neutral_filters_change_nothing(frame):
    assert np.array_equal(apply_filters(frame, Filters()), frame)


@pytest.mark.parametrize("filters", [Filters(brightness=40), Filters(preset="pastel")])
def test_filters_do_not_modify_source(frame, filters):
    before = frame.copy()
    result = apply_filters(frame, filters)
    assert np.array_equal(frame, before)
    assert result.shape == frame.shape
    assert result.dtype == np.uint8


def test_brightness(frame):
    assert apply_filters(frame, Filters(brightness=40)).mean() == pytest.approx(frame.mean() + 40, abs=1)
    assert apply_filters(frame, Filters(brightness=-40)).mean() == pytest.approx(frame.mean() - 40, abs=1)


def test_contrast(frame):
    assert apply_filters(frame, Filters(contrast=40)).std() > frame.std()
    assert apply_filters(frame, Filters(contrast=-40)).std() < frame.std()
    assert apply_filters(frame, Filters(contrast=-100)).std() == 0


def test_saturation(frame):
    gray = apply_filters(frame, Filters(saturation=-100))
    assert np.array_equal(gray[:, :, 0], gray[:, :, 1])
    assert np.array_equal(gray[:, :, 1], gray[:, :, 2])
    vivid = apply_filters(frame, Filters(saturation=50))
    assert (vivid.max(axis=2) - vivid.min(axis=2)).mean() > (frame.max(axis=2) - frame.min(axis=2)).mean()


def test_temperature(frame):
    warm = apply_filters(frame, Filters(temperature=50))
    cool = apply_filters(frame, Filters(temperature=-50))
    assert warm[:, :, 0].mean() > frame[:, :, 0].mean()
    assert warm[:, :, 2].mean() < frame[:, :, 2].mean()
    assert cool[:, :, 0].mean() < frame[:, :, 0].mean()
    assert cool[:, :, 2].mean() > frame[:, :, 2].mean()


def test_values_stay_between_0_and_255():
    white = np.full((4, 4, 3), 250, dtype=np.uint8)
    black = np.full((4, 4, 3), 5, dtype=np.uint8)
    assert apply_filters(white, Filters(brightness=100)).min() == 255
    assert apply_filters(black, Filters(brightness=-100)).max() == 0


def test_presets_are_all_different(frame):
    results = [apply_filters(frame, Filters(preset=preset)) for preset in PRESETS]
    for i in range(len(results)):
        for j in range(i):
            assert not np.array_equal(results[i], results[j])


def test_sliders_are_added_to_preset(frame):
    mono = apply_filters(frame, Filters(preset="mono"))
    brighter = apply_filters(frame, Filters(preset="mono", brightness=30))
    assert brighter.mean() > mono.mean()


def test_float_frames_are_accepted(frame):
    result = apply_filters(frame.astype(float), Filters(preset="mono"))
    assert result.dtype == np.uint8
    assert apply_blur(frame.astype(float), Blur(intensity=50)).dtype == np.uint8


def test_no_blur(frame):
    assert np.array_equal(apply_blur(frame, Blur(intensity=0)), frame)


@pytest.mark.parametrize("kind", ["gaussian", "motion", "radial"])
@pytest.mark.parametrize("background", [False, True])
def test_blur(frame, kind, background):
    before = frame.copy()
    for intensity in (1, 50, 100):
        result = apply_blur(frame, Blur(kind=kind, intensity=intensity, background=background))
        assert result.shape == frame.shape
        assert result.dtype == np.uint8
    assert result.std() < frame.std()
    assert np.array_equal(frame, before)


@pytest.mark.parametrize("kind", ["gaussian", "motion", "radial"])
def test_more_intensity_is_blurrier(frame, kind):
    low = apply_blur(frame, Blur(kind=kind, intensity=20))
    high = apply_blur(frame, Blur(kind=kind, intensity=100))
    assert high.std() < low.std()


def test_motion_blur_is_horizontal(square):
    result = apply_blur(square, Blur(kind="motion", intensity=100))
    assert 0 < result[45, 58, 0] < 255
    assert result[28, 80, 0] == 0


def test_background_blur_keeps_center(frame):
    result = apply_blur(frame, Blur(intensity=100, background=True))
    assert np.array_equal(result[40:50, 70:90], frame[40:50, 70:90])
    assert not np.array_equal(result[:10, :10], frame[:10, :10])


def test_feather_makes_transition_wider(frame):
    hard = apply_blur(frame, Blur(intensity=100, background=True, feather=0))
    soft = apply_blur(frame, Blur(intensity=100, background=True, feather=100))
    full = apply_blur(frame, Blur(intensity=100))
    assert (hard == full).mean() > (soft == full).mean()


@pytest.fixture
def layer():
    return ColorClip((40, 20), color=(255, 0, 0), duration=2).with_position((60, 30))


def test_no_animation(layer):
    assert animate_text(layer, "none") is layer


def test_fade(layer):
    animated = animate_text(layer, "fade")
    assert animated.mask.get_frame(0).max() == 0
    assert 0 < animated.mask.get_frame(0.25).max() < 1
    assert animated.mask.get_frame(1).min() == 1


def test_slide(layer):
    animated = animate_text(layer, "slide")
    assert animated.pos(0) == (-40, 30)
    assert animated.pos(0)[0] < animated.pos(0.25)[0] < 60
    assert animated.pos(1) == (60, 30)


def test_zoom(layer):
    animated = animate_text(layer, "zoom")
    assert animated.get_frame(0).shape == (2, 4, 3)
    assert animated.get_frame(1).shape == (20, 40, 3)
    x, y = animated.pos(0)
    assert (x + 2, y + 1) == pytest.approx((80, 40))
    assert animated.pos(1) == (60, 30)


def test_animation_shorter_than_short_clip(layer):
    animated = animate_text(layer.with_duration(0.2), "slide")
    assert animated.pos(0.2) == (60, 30)


def test_big_blur_is_close_to_real_gaussian():
    rng = np.random.default_rng(1)
    big = cv2.resize(rng.integers(0, 255, (9, 16, 3), dtype=np.uint8), (1280, 720))
    result = apply_blur(big, Blur(intensity=100))
    expected = cv2.GaussianBlur(big, (0, 0), 720 * MAX_BLUR)
    assert result.shape == big.shape
    assert np.abs(result.astype(int) - expected).mean() < 1
