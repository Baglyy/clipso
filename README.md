# Clipso

## Logiciel de montage vidéo

| Catégorie                     | Technologies                                                                                                                                                                                                  |
| ----------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Interface graphique**       | ![PyQt6](https://img.shields.io/badge/PyQt6-41CD52?style=flat-square&logo=qt&logoColor=white)                                                                                                                 |
| **Lecture/Export des vidéos** | ![FFmpeg](https://img.shields.io/badge/FFmpeg-20AB56?style=flat-square&logo=ffmpeg&logoColor=white)                                                                                                           |
| **Analyse des frames**        | ![OpenCV](https://img.shields.io/badge/OpenCV-5C3EE8?style=flat-square&logo=opencv&logoColor=white)                                                                                                           |
| **Effets visuels**            | ![MoviePy](https://img.shields.io/badge/MoviePy-111111?style=flat-square&logo=python&logoColor=white) ![PIL/Pillow](https://img.shields.io/badge/Pillow-3776AB?style=flat-square&logo=python&logoColor=white) |
| **Effets audio**              | ![Audiomentations](https://img.shields.io/badge/Audiomentations-FF6F00?style=flat-square&logo=python&logoColor=white)                                                                                         |

## Architecture MVC

La base de code suit le patron architectural **MVC** afin de séparer clairement la gestion de l'état du montage (modèle), la logique de contrôle des actions utilisateur (contrôleur), et l'affichage (vue). Cette séparation facilite la testabilité de chaque couche indépendamment de l'interface graphique, permet le développement en parallèle des différents modules, et évite le couplage entre la logique métier et le rendu graphique.

## Guide d'Installation

### Prérequis

- Python 3.10 ou plus récent
- Git
- FFmpeg (`sudo apt install ffmpeg`)

### 1. Cloner le projet

```bash
git clone https://github.com/Baglyy/clipso.git
cd clipso
```

### 2. Créer l'environnement virtuel

**Linux**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

> Sur Ubuntu/Debian, si la création échoue, installez d'abord le module venv :
> `sudo apt install python3-venv`

### 3. Installer les dépendances

```bash
pip install -r requirements.txt
```

### 4. Lancer Clipso

```bash
python main.py
```

## Développement

### Outils

On utilise **ruff** pour vérifier et mettre en forme le code, et **pytest** pour les tests.

```bash
pip install -r requirements-dev.txt
```

Avant chaque commit, on lance :

```bash
ruff format .   # remet le code en forme
ruff check .    # cherche les erreurs (imports inutiles, variables pas définies...)
pytest          # lance les tests
```

`pytest` affiche aussi le **coverage** : le pourcentage du code qui est exécuté par les tests, et les lignes qui ne le sont pas (colonne `Missing`). Les fichiers testés à 100 % ne sont pas affichés.

Les tests sont dans `tests/` : `test_format.py` et `test_theme.py` testent les petites fonctions, `test_ui.py` ouvre l'appli sans l'afficher et vérifie que tout marche (navigation, lecture, timeline, propriétés, export).

### Où trouver quoi dans `view/`

| Fichier / dossier              | À quoi ça sert                                                                                |
| ------------------------------ | --------------------------------------------------------------------------------------------- |
| `theme.py`                     | Les couleurs, le chemin vers `assets/` et la fonction `icon()`                                |
| `painting.py`                  | Les dessins réutilisés (formes d'onde, fonds rayés)                                           |
| `format.py`                    | Pour afficher les temps et les valeurs (`00:58`, `5,6 s`, `30 %`...)                          |
| `ui_helpers.py`                | Des petites fonctions pour éviter de répéter le même code sur les boutons et les curseurs     |
| `home/`, `editor/`, `dialogs/` | Les écrans : pour chaque partie, un fichier `.ui` (fait avec Qt Designer) et un fichier `.py` |
| `demo_data.py`                 | Des fausses données pour tester l'interface en attendant le back                              |

Tout ce qui est écrit en dur et qu'on devra remplacer par le back est marqué avec `# TODO:`. Pour tout retrouver : `grep -rn TODO view`.

### Nos règles de code

- Le code est en **anglais** (variables, fonctions, classes), les commentaires et les textes de l'appli sont en **français**.
- Les couleurs viennent toujours de `theme.py` et les icônes passent par `icon()`.
- Le style va dans `assets/styles/clipso.qss`. On utilise `setStyleSheet` seulement quand la couleur change pendant l'exécution.
- On évite les commentaires qui répètent le code : un commentaire sert à expliquer **pourquoi** on fait quelque chose.
