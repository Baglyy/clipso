"""Mise en forme des temps et des valeurs affichées dans l'interface."""


def timecode(seconds: float, fps: int) -> str:
    """00:01:05:12 (heures:minutes:secondes:images)."""
    frames = int(round(seconds * fps))
    s, f = divmod(frames, fps)
    m, s = divmod(s, 60)
    h, m = divmod(m, 60)
    return f"{h:02d}:{m:02d}:{s:02d}:{f:02d}"


def mm_ss(seconds: float) -> str:
    """01:05"""
    minutes, secs = divmod(int(seconds), 60)
    return f"{minutes:02d}:{secs:02d}"


def seconds_text(seconds: float) -> str:
    """5,6 s (virgule française)."""
    return f"{seconds:.1f} s".replace(".", ",")


def percent(value: int) -> str:
    return f"{value} %"


def signed(value: int) -> str:
    """+12, -5 ou 0."""
    return f"{value:+d}" if value else "0"
