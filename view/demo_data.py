"""Données de démonstration, en attendant les modèles."""
# TODO: fichier entier à supprimer quand le modèle et le controller fourniront les projets

RECENT_PROJECTS = [
    ("Vacances à Biarritz", "Modifié il y a 2 h · 16:9 · 1080p", "00:58", "#5B7898"),
    ("Anniversaire de Mamie", "Modifié hier · 16:9 · 1080p", "03:12", "#AE7657"),
    ("Tuto crêpes au caramel", "Modifié il y a 3 jours · 9:16 · 1080p", "05:40", "#4E8885"),
    ("Vlog de la rentrée", "Modifié le 12 sept. · 16:9 · 720p", "02:05", "#6A8A5A"),
    ("Match du dimanche", "Modifié le 8 sept. · 16:9 · 1080p", "01:30", "#76604F"),
    ("Court-métrage TP vidéo", "Modifié le 2 sept. · 16:9 · 1080p", "07:48", "#5B7898"),
]

MEDIA = [
    {"name": "plage_drone.mp4", "kind": "video", "duration": "0:14", "color": "#5E7C98", "used": True},
    {"name": "surf_ralenti.mp4", "kind": "video", "duration": "0:15", "color": "#4E8885", "used": True},
    {"name": "coucher_soleil.mp4", "kind": "video", "duration": "0:15", "color": "#AE7657", "used": True},
    {"name": "amis_feu.mp4", "kind": "video", "duration": "0:14", "color": "#76604F", "used": True},
    {"name": "randonnee.mp4", "kind": "video", "duration": "0:32", "color": "#6A8A5A", "used": False},
    {"name": "voix_off.wav", "kind": "audio", "duration": "0:25", "used": True},
    {"name": "rires.wav", "kind": "audio", "duration": "0:07", "used": True},
    {"name": "musique_chill.mp3", "kind": "audio", "duration": "0:58", "used": True},
    {"name": "logo_club.png", "kind": "image", "duration": "", "color": "#D9B8C8", "used": True},
    {"name": "photo_groupe.jpg", "kind": "image", "duration": "", "color": "#C9A27E", "used": False},
]

DURATION = 58.0
PLAYHEAD = 32.63

TRACKS = [
    {
        "name": "Vidéo 2",
        "kind": "overlay",
        "clips": [
            {"kind": "text", "name": "Titre « Été 2026 »", "text": "Été 2026", "start": 2.9, "duration": 5.6},
            {"kind": "text", "name": "Titre « Été 2026 »", "text": "Été 2026", "start": 8.5, "duration": 1.4},
            {"kind": "image", "name": "logo_club.png", "start": 31.0, "duration": 10.0},
        ],
    },
    {
        "name": "Vidéo 1",
        "kind": "video",
        "clips": [
            {"kind": "video", "name": "plage_drone.mp4", "start": 0.0, "duration": 14.0, "color": "#5E7C98"},
            {"kind": "video", "name": "surf_ralenti.mp4", "start": 14.0, "duration": 15.0, "color": "#4E8885"},
            {"kind": "video", "name": "coucher_soleil.mp4", "start": 29.0, "duration": 15.0, "color": "#AE7657"},
            {"kind": "video", "name": "amis_feu.mp4", "start": 44.0, "duration": 14.0, "color": "#76604F"},
        ],
    },
    {
        "name": "Audio 1",
        "kind": "audio",
        "icon": "microphone",
        "clips": [
            {"kind": "audio", "name": "voix_off.wav", "start": 2.0, "duration": 25.0},
            {"kind": "audio", "name": "rires.wav", "start": 35.2, "duration": 7.0},
        ],
    },
    {
        "name": "Audio 2",
        "kind": "audio",
        "icon": "music-note",
        "clips": [
            {"kind": "audio", "name": "musique_chill.mp3", "start": 0.0, "duration": 58.0},
        ],
    },
]

SELECTED_CLIP = TRACKS[0]["clips"][2]
SELECTED_TAB = "blur"
