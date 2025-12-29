"""
Splash screen module for game initialization.
"""

__license__ = "Regarder le fichier LICENSE.txt dans le répertoire racine du projet."
__author__ = "PFLIEGER-CHAKMA Nathan alias J0ytheC0de"

from pathlib import Path
from panda3d.core import (
    CardMaker,
    TransparencyAttrib,
    Texture,
    NodePath,
)
from direct.interval.IntervalGlobal import Sequence, LerpFunc, Func
from Assets.utils import profile


class LogoSplash:
    """
    Handles the logo splash screen animation.
    """

    @profile
    def __init__(self, parent):
        """
        Initialize the splash screen.

        Args:
            parent: The parent application instance.
        """
        self.parent = parent
        self.logo_card: NodePath = None
        self.bg_card: NodePath = None

    @profile
    def setup(self):
        """
        Set up the splash screen elements and animation.

        Returns:
            Sequence: The animation sequence.
        """
        # Create fullscreen black background
        cm_bg = CardMaker("bg_card")
        cm_bg.setFrameFullscreenQuad()
        self.bg_card = self.parent.render2d.attachNewNode(cm_bg.generate())
        self.bg_card.setColor(0, 0, 0, 1)
        self.bg_card.setBin("background", 0)
        self.bg_card.setDepthWrite(False)
        self.bg_card.setDepthTest(False)

        # Load and setup logo texture
        asset_path = Path("Assets/icon/assets")
        tex = self.parent.loader.loadTexture(str(asset_path / "panda3d_logo_panda.png"))
        tex.setMinfilter(Texture.FTLinear)
        tex.setMagfilter(Texture.FTLinear)

        tex_x = tex.getXSize()
        tex_y = tex.getYSize()
        aspect_ratio = tex_x / tex_y

        # Create logo quad with correct aspect ratio
        # Use smaller size to fit nicely on screen
        max_height = 0.6  # Maximum height (60% of screen height)
        max_width = 0.8   # Maximum width (80% of screen width)
        
        # Calculate dimensions maintaining aspect ratio
        if aspect_ratio > max_width / max_height:
            # Width-limited
            width = max_width
            height = max_width / aspect_ratio
        else:
            # Height-limited
            height = max_height
            width = max_height * aspect_ratio

        cm_logo = CardMaker("logo_card")
        cm_logo.setFrame(-width / 2, width / 2, -height / 2, height / 2)

        self.logo_card = self.parent.render2d.attachNewNode(cm_logo.generate())
        self.logo_card.setTransparency(TransparencyAttrib.MAlpha)
        self.logo_card.setTexture(tex)
        self.logo_card.setColorScale(1, 1, 1, 0)  # Start invisible
        self.logo_card.setBin("fixed", 1)

        # Create fade-in and fade-out animation
        def fade_in(t):
            self.logo_card.setColorScale(1, 1, 1, t)

        def fade_out(t):
            self.logo_card.setColorScale(1, 1, 1, 1 - t)

        interval = Sequence(
            LerpFunc(fade_in, fromData=0, toData=1, duration=1.5),
            LerpFunc(fade_out, fromData=0, toData=1, duration=1.5),
        )

        return interval

    def cleanup(self):
        """Clean up splash screen elements."""
        if self.logo_card:
            self.logo_card.removeNode()
        if self.bg_card:
            self.bg_card.removeNode()