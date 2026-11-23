"""Média importé dans un projet : un fichier vidéo, audio ou image sur le disque."""

import subprocess
from dataclasses import dataclass, field
from pathlib import Path

import cv2
import imageio_ffmpeg
import numpy as np
from moviepy import AudioFileClip, VideoFileClip
from PIL import Image

VIDEO_EXTENSIONS = {".mp4", ".mov", ".webm", ".mkv", ".avi"}
AUDIO_EXTENSIONS = {".wav", ".mp3", ".ogg", ".flac", ".m4a"}
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}
THUMBNAIL_HEIGHT = 120
PEAKS = 400  # nombre de barres de la forme d'onde
PEAKS_SAMPLE_RATE = 4000


@dataclass
class Media:
    path: Path
    kind: str  # "video", "audio" ou "image"
    duration: float = 0.0
    width: int = 0
    height: int = 0
    has_audio: bool = False
    thumbnail: np.ndarray | None = field(default=None, repr=False, compare=False)
    # forme d'onde, valeurs entre 0 et 1
    peaks: list[float] = field(default_factory=list, repr=False, compare=False)
    max_volume: float = 1.0  # sert à normaliser le son

    @property
    def name(self) -> str:
        return self.path.name

    @classmethod
    def from_file(cls, path: str | Path) -> "Media":
        """Lève ValueError si le fichier n'est pas lisible."""
        path = Path(path)
        kind = kind_of(path)
        try:
            if kind == "video":
                with VideoFileClip(str(path)) as clip:
                    width, height = clip.size
                    media = cls(path, kind, clip.duration, width, height, clip.audio is not None)
                media.thumbnail = video_thumbnail(path, media.duration)
                if media.has_audio:
                    media.peaks, media.max_volume = audio_peaks(path)
                return media
            if kind == "audio":
                with AudioFileClip(str(path)) as clip:
                    duration = clip.duration
                peaks, max_volume = audio_peaks(path)
                return cls(path, kind, duration, has_audio=True, peaks=peaks, max_volume=max_volume)
            with Image.open(path) as image:
                width, height = image.size
                return cls(path, kind, width=width, height=height, thumbnail=image_thumbnail(image))
        except (OSError, KeyError, subprocess.CalledProcessError) as error:
            raise ValueError(f"Impossible de lire {path.name}") from error


def kind_of(path: Path) -> str:
    extension = path.suffix.lower()
    if extension in VIDEO_EXTENSIONS:
        return "video"
    if extension in AUDIO_EXTENSIONS:
        return "audio"
    if extension in IMAGE_EXTENSIONS:
        return "image"
    raise ValueError(f"Format non pris en charge : {path.name}")


def video_thumbnail(path: Path, duration: float) -> np.ndarray | None:
    # à 10 % de la vidéo, car la première image est souvent noire
    capture = cv2.VideoCapture(str(path))
    try:
        capture.set(cv2.CAP_PROP_POS_MSEC, duration * 0.1 * 1000)
        ok, frame = capture.read()
    finally:
        capture.release()
    if not ok:
        return None
    # OpenCV lit les couleurs en BGR
    return _resize(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))


def image_thumbnail(image: Image.Image) -> np.ndarray:
    return _resize(np.asarray(image.convert("RGB")))


def audio_peaks(path: Path) -> tuple[list[float], float]:
    # FFmpeg convertit le son en mono, 4000 échantillons par seconde, en nombres à virgule
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    command = [
        ffmpeg,
        "-loglevel",
        "error",
        "-i",
        str(path),
        "-ac",
        "1",
        "-ar",
        str(PEAKS_SAMPLE_RATE),
        "-f",
        "f32le",
        "-",
    ]
    output = subprocess.run(command, check=True, capture_output=True).stdout
    samples = np.abs(np.frombuffer(output, dtype=np.float32))
    if samples.size == 0:
        return [], 1.0
    chunks = np.array_split(samples, min(PEAKS, samples.size))
    peaks = np.array([chunk.max() for chunk in chunks])
    loudest = float(peaks.max())
    if loudest == 0:
        return peaks.tolist(), 1.0
    return (peaks / loudest).tolist(), loudest


def _resize(frame: np.ndarray) -> np.ndarray:
    height, width = frame.shape[:2]
    new_width = max(1, round(width * THUMBNAIL_HEIGHT / height))
    return np.ascontiguousarray(cv2.resize(frame, (new_width, THUMBNAIL_HEIGHT), interpolation=cv2.INTER_AREA))
