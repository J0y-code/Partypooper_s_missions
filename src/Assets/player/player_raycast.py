"""
Player raycast functionality for interaction detection.
"""

__license__ = "Regarder le fichier LICENSE.txt dans le répertoire racine du projet."
__author__ = "PFLIEGER-CHAKMA Nathan alias J0ytheC0de"

from panda3d.core import Vec3, BitMask32, LineSegs


class PlayerRaycast:
    """
    Handles raycasting for player interactions.
    """

    def __init__(self, render, camera, bullet_world, max_distance=4.0, debug=False):
        """
        Initialize the raycast system.

        Args:
            render: The render node.
            camera: The camera to cast rays from.
            bullet_world: The Bullet physics world.
            max_distance: Maximum raycast distance.
            debug: Whether to show debug visualization.
        """
        self.render = render
        self.camera = camera
        self.world = bullet_world
        self.max_distance = max_distance
        self.debug = debug

        self.debug_np = None
        if debug:
            self._init_debug()

    def _init_debug(self):
        """Initialize debug visualization."""
        self.ls = LineSegs()
        self.ls.setThickness(2)

    def interact(self):
        """
        Perform interaction raycast.

        Returns:
            bool: True if interaction was successful.
        """
        p_from = self.camera.getPos(self.render)
        direction = self.camera.getQuat(self.render).getForward()
        p_to = p_from + direction * self.max_distance

        if self.debug:
            self._update_debug(p_from, p_to)

        result = self.world.rayTestClosest(
            p_from,
            p_to,
            BitMask32.bit(1)  # Same layer as doors
        )

        if not result.hasHit():
            return False

        body = result.getNode()
        if not body:
            return False

        # Check for interactable object
        if body.hasPythonTag("object"):
            obj = body.getPythonTag("object")
            if hasattr(obj, "toggle"):
                obj.toggle()
                return True

        return False

    def _update_debug(self, p_from, p_to):
        """Update debug visualization."""
        if self.debug_np:
            self.debug_np.removeNode()

        self.ls.reset()
        self.ls.setColor(1, 0, 0, 1)
        self.ls.moveTo(p_from)
        self.ls.drawTo(p_to)

        node = self.ls.create()
        self.debug_np = self.render.attachNewNode(node)

    def update_debug_smoothly(self, task):
        """
        Update debug visualization smoothly.

        Args:
            task: The task object.

        Returns:
            Task.cont or Task.done
        """
        if not self.debug:
            return task.done
        p_from = self.camera.getPos(self.render)
        direction = self.camera.getQuat(self.render).getForward()
        p_to = p_from + direction * self.max_distance
        self._update_debug(p_from, p_to)
        return task.cont