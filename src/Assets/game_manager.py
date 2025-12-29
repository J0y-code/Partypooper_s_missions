"""
Game manager for handling game setup and loading.
"""

__license__ = "Regarder le fichier LICENSE.txt dans le répertoire racine du projet."
__author__ = "PFLIEGER-CHAKMA Nathan alias J0ytheC0de"

from pathlib import Path
from panda3d.core import (
    Filename,
    AmbientLight,
    PointLight,
    Vec3,
    Vec4,
    Texture,
    Shader,
    CardMaker,
    NodePath,
    TransparencyAttrib,
)
from direct.gui.OnscreenText import OnscreenText
from direct.gui.DirectGui import DirectWaitBar
from direct.task import Task
from Assets.utils import profile


class GameManager:
    """
    Manages game loading, menu setup, and post-processing effects.
    """

    @profile
    def __init__(self, parent):
        """
        Initialize the game manager.

        Args:
            parent: The parent application instance.
        """
        self.parent = parent
        self.menumodel = None
        self.lights = []
        self.buffer = None
        self.buffer_cam = None
        self.card = None
        self.shader = None
        self.vhs_strength = 0.75

    @profile
    def setup_menu(self, task):
        """
        Set up the menu scene.

        Args:
            task: The task object.

        Returns:
            Task.done
        """
        # Load menu model
        self.menumodel = self.parent.loader.loadModel("Assets/firstmodels/menu.bam")
        self.menumodel.reparentTo(self.parent.render)

        # Camera setup
        self.parent.camLens.setFov(120)
        self.parent.camLens.setNearFar(0.1, 100000)
        self.parent.cam.setPos(0, -4, 1)

        # Lamp lighting
        self.lampe = self.menumodel.find("**/lampe")
        self.plight = PointLight("plight")
        self.lampe.setLightOff()
        self.plight.setColor(Vec4(0.2, 0.2, 0.2, 1))
        self.plight.setAttenuation((1, 0.2, 0.1))
        self.plight_node = self.lampe.attachNewNode(self.plight)
        self.parent.render.setLight(self.plight_node)

        # Ambient light
        malight = AmbientLight('ambient')
        malight.setColor(Vec4(0.0, 0.0, 0.0, 1))
        malnp = self.parent.render.attachNewNode(malight)
        self.parent.render.setLight(malnp)

        self.lights = [self.plight_node, malnp]

        # Initialize variables
        self.parent.last_knockback_time = 0
        self.parent.knockback_cooldown = 0.5

        # Setup post-processing
        self._setup_post_processing()

        # Start background music
        self.theme = self.parent.loader.loadMusic("Assets/music/theme.mp3")
        self.theme.setLoop(True)
        self.theme.play()

        return Task.done

    def _setup_post_processing(self):
        """Set up post-processing effects (VHS shader)."""
        # Create offscreen buffer
        RTT_W, RTT_H = 320, 240
        RTT_FILTER = 'linear'

        self.buffer = self.parent.win.makeTextureBuffer("SceneBuffer", RTT_W, RTT_H)
        self.buffer.setClearColor(Vec4(0, 0, 0, 1))
        self.buffer.getDisplayRegion(0).setClearColorActive(True)

        buf_tex = self.buffer.getTexture()
        buf_tex.setWrapU(Texture.WM_clamp)
        buf_tex.setWrapV(Texture.WM_clamp)

        if RTT_FILTER == 'nearest':
            buf_tex.setMagfilter(Texture.FTNearest)
            buf_tex.setMinfilter(Texture.FTNearest)
        else:
            buf_tex.setMagfilter(Texture.FTLinear)
            buf_tex.setMinfilter(Texture.FTLinear)

        # Attach camera to buffer
        self.buffer_cam = self.parent.makeCamera(self.buffer)
        self.buffer_cam.reparentTo(self.parent.cam)

        lens = self.buffer_cam.node().getLens()
        lens.setFov(120)
        try:
            lens.setAspectRatio(float(RTT_W) / float(RTT_H))
        except Exception:
            pass
        lens.setNearFar(0.01, 100000)

        # Create fullscreen quad for shader
        cm = CardMaker("fullscreen_quad")
        cm.setFrameFullscreenQuad()
        self.card = self.parent.render2d.attachNewNode(cm.generate())
        self.card.setTransparency(False)
        self.card.setDepthTest(False)
        self.card.setDepthWrite(False)
        self.card.setBin("fixed", 0)

        # Load and apply VHS shader
        self.shader = Shader.load(
            Shader.SL_GLSL,
            "Assets/shader/VHS/vhs.vert",
            "Assets/shader/VHS/vhs.frag"
        )
        self.card.setShader(self.shader)
        self.card.setShaderInput("sceneTex", self.buffer.getTexture())
        self.card.setShaderInput("curvature", 0.12)
        self.card.setShaderInput("vhs_strength", self.vhs_strength)

        # Start update tasks
        self.parent.taskMgr.add(self.update_shader, "update_shader")
        self.parent.taskMgr.add(self.update_light, "LightUpdateTask")

    @profile
    def load_game(self, task):
        """
        Load the main game assets.

        Args:
            task: The task object.

        Returns:
            Task.done
        """
        if task.time > 0:
            # Load player
            from Assets.player.player import Player
            self.parent.player = Player(parentClass=self.parent)

            # Load terrain
            from Assets.levels.terrain.terrain import Terrain
            self.parent.terrain = Terrain(parent=self.parent)

            # Setup game lights
            self.setup_game_lights()

            # Clean up loading screen
            self.loading_text.destroy()
            self.progress_bar.destroy()

            self.parent.mouse_active = False
            self.theme.stop()

            return Task.done

        return task.cont

    def setup_game_lights(self):
        """Set up lighting for the game scene."""
        alight = AmbientLight('ambient')
        alight.setColor(Vec4(0., 0., 0., 1))
        alnp = self.parent.render.attachNewNode(alight)
        self.parent.render.setLight(alnp)

    def update_shader(self, task):
        """
        Update shader uniforms.

        Args:
            task: The task object.

        Returns:
            Task.cont
        """
        from panda3d.core import ClockObject
        t = ClockObject.getGlobalClock().getFrameTime()
        self.card.setShaderInput("time", t)
        self.card.setShaderInput("vhs_strength", self.vhs_strength)
        return task.cont

    def update_light(self, task):
        """
        Update flickering light effect.

        Args:
            task: The task object.

        Returns:
            Task.cont or Task.done
        """
        if not hasattr(self, "plight") or not self.plight:
            return Task.done

        import random
        base_intensity = 0.2
        flicker_duration = 0.2
        cooldown_min = 0.2
        cooldown_max = 2

        if not hasattr(self, "_flicker_state"):
            self._flicker_state = "idle"
            self._next_change = 0.0

        t = task.time

        if self._flicker_state == "idle":
            if t >= self._next_change:
                self._flicker_state = "flickering"
                self._flicker_end = t + flicker_duration
            else:
                self.plight.setColor(Vec4(base_intensity, base_intensity, base_intensity, 1))
                if hasattr(self, 'lampe'):
                    self.lampe.setColor(1, 1, 1, 1)
                return Task.cont

        if self._flicker_state == "flickering":
            intensity = random.randint(100, 1000) / 10000.0
            self.plight.setColor(Vec4(intensity, intensity, intensity, 1))
            if hasattr(self, 'lampe'):
                self.lampe.setColor(intensity / 1000, intensity / 1000, intensity / 1000, 1)

            if t >= self._flicker_end:
                self._flicker_state = "idle"
                self._next_change = t + random.uniform(cooldown_min, cooldown_max)

        return Task.cont

    def start_loading_screen(self):
        """Display the loading screen."""
        self.parent.cam.setPos(0, 0, 0)

        self.loading_text = OnscreenText(
            text="Chargement...",
            pos=(0, 0),
            scale=0.1,
            fg=(1, 1, 1, 1),
            mayChange=True,
        )
        self.progress_bar = DirectWaitBar(
            text="Chargement en cours",
            value=0,
            pos=(0, 0, -0.8),
            barColor=(0.2, 0.7, 0.2, 1),
            scale=0.5,
        )

        self.parent.taskMgr.doMethodLater(0.1, self.load_game, "loadGame")

    def cleanup_menu(self):
        """Clean up menu resources."""
        if self.menumodel:
            self.menumodel.removeNode()

        for light in self.lights:
            self.parent.render.clearLight(light)
            light.removeNode()
        self.lights = []

    def cleanup(self):
        """Clean up all resources."""
        self.cleanup_menu()
        if hasattr(self, 'theme'):
            self.theme.stop()