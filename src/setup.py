__license__ = "Regarder le fichier LICENSE.txt dans le répertoire racine du projet."
__author__ = "PFLIEGER-CHAKMA Nathan alias J0ytheC0de"

from setuptools import setup

setup(
    name="PMB",
    version="0.0.1",
    options={
        "build_apps": {
            "gui_apps": {
                "Partypoopers_Missions": "main.py",
            },

            "log_filename": "$USER_APPDATA/Partypoopers_Missions/output.txt",

            "include_patterns": [
                "Assets/levels/terrain/**/*.bam",
                "Assets/levels/terrain/**/*",
                "Assets/levels/terrain/*.py",
                "Assets/levels/terrain/models/pbrtex/*",
                "Assets/player/*.py",
                "Assets/player/**/*",
                "Assets/player/**/**/*",
                "Assets/modules/pathfinding/*",
                "Assets/main_ui/*",
                "Assets/shader/VHS/*",
                "Assets/music/*.mp3",
                "Assets/firstmodels/*.bam",
                "Assets/icon/assets/*",
                "*.prc",
            ],

            "bam_model_extensions": [".gltf", ".egg", ".glb"],

            "plugins": [
                "pandagl", "pandax9", "p3ptloader",
                "p3assimp", "p3openal_audio", "p3ffmpeg",
            ],

            "platforms": ["win_amd64"],

            "icons": {
                "Partypoopers_Missions": ["inbuild.png"],
            },
        }
    },
)
