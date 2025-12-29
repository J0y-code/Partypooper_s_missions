# -- Coding: UTF-8 --
# -- Using python 3.12.8 --
#information sur l'auteur et la license
__license__ = "Regarder le fichier LICENSE.txt dans le répertoire racine du projet."
__author__ = "PFLIEGER-CHAKMA Nathan alias J0ytheC0de"

#Imports
import sys
import os
if getattr(sys, "frozen", False):
    os.chdir(os.path.dirname(sys.executable))

from panda3d.core import load_prc_file
from panda3d.bullet import BulletWorld
load_prc_file("MyConfig.prc")

from direct.showbase.ShowBase import ShowBase
from direct.showbase.ShowBaseGlobal import globalClock
from direct.task import Task
from direct.interval.FunctionInterval import Func
from panda3d.core import Vec3

import simplepbr

from Assets.splash_screen import LogoSplash
from Assets.game_manager import GameManager
from Assets.network_manager import NetworkManager
from Assets.main_ui.menu import Menu
from Assets.utils import profile

# --- Classe principale de l'application ---
class App(ShowBase):
    @profile
    def __init__(self):
        """Constructeur de l'application principale."""
        ShowBase.__init__(self)  # Initialise Panda3D

        # --- Démarrage du Splash Screen ---
        splash = LogoSplash(self)  # Crée l'objet splash
        interval = splash.setup()  # Prépare l'animation
        interval.start()  # Lance l'animation

        # --- Configuration initiale ---
        self.disable_mouse()  # Désactive le contrôle caméra par défaut de Panda
        simplepbr.init(
            enable_shadows=False,
            max_lights=30,
            #use_normal_maps=True,
            enable_fog=True,

            # Normal maps
            #calculate_normalmap_blue=True,

            # PBR réaliste
            use_occlusion_maps=True,
            use_emission_maps=True,
            exposure=-0.01,
            msaa_samples=4,
            use_330=True,
        )

        # Planifie le lancement du menu après 4.0 secondes
        # (laisse le temps au splash de se terminer)
        self.taskMgr.doMethodLater(4.0, self.setup_menu, "setup_menu_task")

        self.bullet_world = BulletWorld()
        self.bullet_world.setGravity(Vec3(0, 0, -9.81))
        self.taskMgr.add(self.update_physics, "bullet_physics")

        # Initialize managers
        self.game_manager = GameManager(self)
        self.network_manager = None  # Will be initialized for multiplayer

    @profile
    def setup_menu(self, task):
        """Charge et configure la scène du menu principal."""
        self.game_manager.setup_menu(task)

        # Initialise la logique du menu UI
        self.menu = Menu(parent=self, start_callback=self.start_game)

        # Bind de la touche "escape"
        self.accept("escape", self.quit_game)

        return Task.done

    @profile
    def load(self):
        """Prépare le chargement du jeu (nettoyage + écran de chargement)."""

        # --- Nettoyage de la scène du menu ---
        self.game_manager.cleanup_menu()

        # --- Affichage de l'écran de chargement ---
        self.game_manager.start_loading_screen()

        # Détruit l'interface (GUI) du menu
        self.menu.destroy()

    @profile
    def start_game(self, mode, ip=None, port=None):
        """
        Point d'entrée appelé par le menu pour démarrer le jeu.
        mode = "solo" ou "multi"
        ip/port = fournis si mode == "multi"
        """
        print(f"[MENU] Start mode={mode}  ip={ip}  port={port}")

        # Sauvegarde le mode de jeu
        self.game_mode = mode

        # Lance la séquence de chargement (écran + assets)
        self.load()

        # Si mode multijoueur, initialise le réseau
        if mode == "multi":
            try:
                self.network_manager = NetworkManager(self, server_ip=ip, server_port=port)
            except Exception as e:
                print("Erreur réseau :", e)
        else:
            print("Mode solo → aucun réseau.")

    def update_shader(self, task):
        """Met à jour les variables (uniforms) du shader à chaque frame."""
        return self.game_manager.update_shader(task)

    def update_light(self, task):
        """Tâche pour faire clignoter la lumière du menu (flickering)."""
        return self.game_manager.update_light(task)

    def update_physics(self, task):
        """Update physics simulation."""
        dt = globalClock.getDt()
        self.bullet_world.doPhysics(dt, 4, 1.0 / 240.0)
        return Task.cont

    def quit_game(self):
        """Fonction appelée pour quitter le jeu."""
        if self.network_manager:
            self.network_manager.cleanup()
        self.userExit()  # Fonction propre de Panda3D pour fermer l'application


# --- Point d'entrée principal de l'application ---
if __name__ == "__main__":
    app = App()  # Crée une instance de l'application
    app.disable_mouse()  # (Redondant, déjà dans __init__ mais OK)

    app.run()  # Lance la boucle principale de Panda3D