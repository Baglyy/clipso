import os

import pytest

# pas de fenêtre à l'écran pendant les tests (marche aussi sans affichage, ex. en CI)
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


@pytest.fixture(autouse=True)
def _qapp(qapp):
    """Qt a besoin d'une QApplication pour créer des pixmaps, icônes et widgets."""


@pytest.fixture(scope="session")
def media_files(tmp_path_factory):
    import subprocess

    import imageio_ffmpeg
    from PIL import Image

    folder = tmp_path_factory.mktemp("media")
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    video, sound, image = folder / "clip.mp4", folder / "son.wav", folder / "logo.png"
    lavfi = ["-f", "lavfi", "-i"]
    subprocess.run(
        [ffmpeg, "-loglevel", "error", *lavfi, "testsrc=size=160x120:rate=10", *lavfi, "sine=frequency=440"]
        + ["-t", "1", "-pix_fmt", "yuv420p", str(video)],
        check=True,
    )
    subprocess.run([ffmpeg, "-loglevel", "error", *lavfi, "sine=frequency=660", "-t", "0.5", str(sound)], check=True)
    Image.new("RGB", (40, 20), "red").save(image)
    return {"video": video, "audio": sound, "image": image}
