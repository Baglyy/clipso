"""Aperçu du montage : l'image à un instant donné, calculée comme à l'export."""

import numpy as np

from model.export import build_video, close_sources
from model.project import Project

# assez net pour l'écran, et bien plus rapide que du 1080p
PREVIEW_RESOLUTION = 360


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
            self.video = build_video(project, project.frame_size(self.resolution), self.sources)

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
