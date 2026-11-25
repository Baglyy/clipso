"""Aperçu du montage : l'image et le son à un instant donné, calculés comme à l'export."""

import numpy as np

from model.export import audible_clips, build_sound, build_video, close_sources
from model.project import Project

# assez net pour l'écran, et bien plus rapide que du 1080p
PREVIEW_RESOLUTION = 360
SAMPLE_RATE = 44100
CHANNELS = 2
# moviepy échoue si on lit d'un coup plus de la moitié d'un fichier court (bruitages)
READ_SIZE = 441


class PreviewRenderer:
    """Assembler le montage est lent (chaque vidéo est ouverte avec FFmpeg) : on le garde
    entre deux images et on ne le refait que si le projet change, avec rebuild()."""

    def __init__(self, resolution: int = PREVIEW_RESOLUTION):
        self.resolution = resolution
        self.video = None
        self.sources = []

    def rebuild(self, project: Project):
        self.close()
        if project.duration > 0:
            self.video = build_video(project, project.frame_size(self.resolution), self.sources, with_audio=False)

    def frame(self, time: float) -> np.ndarray | None:
        if self.video is None:
            return None
        # moviepy plante si on demande l'image pile à la fin
        time = min(max(time, 0.0), self.video.duration - 0.01)
        return self.video.get_frame(time).astype(np.uint8)

    def close(self):
        close_sources(self.sources)
        self.sources = []
        self.video = None


class AudioRenderer:
    """Mixe le son du montage par petits morceaux, en 16 bits stéréo."""

    def __init__(self):
        self.sounds = []
        self.sources = []

    def rebuild(self, project: Project):
        self.close()
        for clip in audible_clips(project):
            try:
                self.sounds.append(build_sound(clip, self.sources))
            except Exception:
                # fichier déplacé ou abîmé : on garde le son des autres clips
                continue

    def samples(self, first: int, count: int) -> np.ndarray:
        """Échantillons à partir du numéro first. Après la fin du montage, c'est du silence."""
        pieces = [
            self._mix(start, min(READ_SIZE, first + count - start)) for start in range(first, first + count, READ_SIZE)
        ]
        return (np.clip(np.concatenate(pieces), -1, 1) * 32767).astype(np.int16)

    def _mix(self, first: int, count: int) -> np.ndarray:
        times = np.arange(first, first + count) / SAMPLE_RATE
        mix = np.zeros((count, CHANNELS))
        for sound in self.sounds:
            inside = (times >= sound.start) & (times < sound.end)
            if not inside.any():
                continue
            try:
                mix[inside] += sound.get_frame(times[inside] - sound.start)
            except Exception:
                # moviepy refuse par exemple un temps juste après la fin du fichier
                continue
        return mix

    def close(self):
        close_sources(self.sources)
        self.sources = []
        self.sounds = []
