"""
Network manager for multiplayer functionality.
"""

__license__ = "Regarder le fichier LICENSE.txt dans le répertoire racine du projet."
__author__ = "PFLIEGER-CHAKMA Nathan alias J0ytheC0de"

import socket
import threading
import json
from queue import Queue, Empty
from panda3d.core import Vec3, ClockObject
from Assets.utils import profile, get_local_ip


class NetworkManager:
    """
    Handles network communication for multiplayer game.
    """

    CLIENT_TIMEOUT = 3.0  # seconds before considering a remote player disconnected

    @profile
    def __init__(self, parent, server_ip="192.168.1.155", server_port=5000):
        """
        Initialize the network manager.

        Args:
            parent: The parent application instance.
            server_ip: Server IP address.
            server_port: Server port.
        """
        self.parent = parent
        self.server_addr = (server_ip, server_port)

        # Socket setup
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(("", 0))
        self.sock.setblocking(False)

        # Client identification
        self.local_ip = get_local_ip()
        self.local_port = self.sock.getsockname()[1]
        self.local_id = f"{self.local_ip}:{self.local_port}"

        print(f"[NET] Local ID = {self.local_id}")

        # Threading and queues
        self.net_queue = Queue()
        self.remote_players = {}

        # Start network listener thread
        threading.Thread(target=self._network_listener, daemon=True).start()

        # Start network update task
        self.parent.taskMgr.doMethodLater(0.01, self._network_update, "network_update")

    def _network_listener(self):
        """
        Network listener thread that receives messages and puts them in the queue.
        """
        while True:
            try:
                data, addr = self.sock.recvfrom(4096)
                msg = json.loads(data.decode())
                self.net_queue.put(msg)
            except BlockingIOError:
                # Normal when no data available
                import time
                time.sleep(0.001)
                continue
            except Exception as e:
                print(f"[NET] Listener error: {e}")
                import time
                time.sleep(0.01)

    def _network_update(self, task):
        """
        Panda3D task that processes network messages and sends local position.

        Args:
            task: The task object.

        Returns:
            Task.cont to continue the task.
        """
        now = ClockObject.getGlobalClock().getRealTime()

        # Send local position
        if hasattr(self.parent, "player"):
            try:
                pos = self.parent.player.controller_np.getPos()
                packet = json.dumps({
                    "type": "pos",
                    "id": self.local_id,
                    "x": pos.x,
                    "y": pos.y,
                    "z": pos.z
                }).encode()
                self.sock.sendto(packet, self.server_addr)
            except Exception as e:
                print(f"[NET] Send error: {e}")

        # Process received messages
        self._process_messages(now)

        # Interpolate remote players and clean up inactive ones
        self._update_remote_players(now)

        return task.again

    def _process_messages(self, now):
        """
        Process all messages in the network queue.

        Args:
            now: Current time.
        """
        while True:
            try:
                msg = self.net_queue.get_nowait()
            except Empty:
                break

            msg_type = msg.get("type", "")

            if msg_type == "players":
                self._handle_players_list(msg, now)
            elif msg_type in ("door_toggle", "door_sync"):
                self._handle_door_sync(msg)

    def _handle_players_list(self, msg, now):
        """
        Handle the players list message.

        Args:
            msg: The message containing player data.
            now: Current time.
        """
        server_players = set()

        for p in msg["players"]:
            pid = p["id"]
            server_players.add(pid)

            if pid == self.local_id:
                continue

            x, y, z = p["x"], p["y"], p["z"]

            if pid not in self.remote_players:
                # New player
                print(f"[NET] New player connected: {pid}")
                model = self.parent.loader.loadModel("Assets/player/models/playertest.egg")
                model.reparentTo(self.parent.render)
                model.setPos(x, y, z)
                model.setScale(1)

                self.remote_players[pid] = {
                    "node": model,
                    "target_pos": Vec3(x, y, z),
                    "last_update": now
                }
            else:
                # Update existing player
                self.remote_players[pid]["target_pos"] = Vec3(x, y, z)
                self.remote_players[pid]["last_update"] = now

        # Remove disconnected players
        for pid in list(self.remote_players.keys()):
            if pid not in server_players:
                print(f"[NET] Player disconnected: {pid}")
                self.remote_players[pid]["node"].removeNode()
                del self.remote_players[pid]

        # Handle door states
        doors = msg.get("doors", {})
        for door_id_str, state in doors.items():
            try:
                self._sync_door(door_id_str, state)
            except Exception as e:
                print(f"[NET] Door sync error {door_id_str}: {e}")

    def _handle_door_sync(self, msg):
        """
        Handle door synchronization message.

        Args:
            msg: The door sync message.
        """
        door_id = msg.get("door_id")
        state = msg.get("state")
        if door_id is not None and state is not None:
            try:
                self._sync_door(door_id, state)
            except Exception as e:
                print(f"[NET] Door sync error {door_id}: {e}")

    def _sync_door(self, door_id, state):
        """
        Synchronize door state with the server.

        Args:
            door_id: The door ID.
            state: The door state (True for open, False for closed).
        """
        if not hasattr(self.parent, "terrain"):
            return

        try:
            door_id_int = int(door_id)
        except Exception:
            door_id_int = door_id

        porte_obj = None
        for p in self.parent.terrain.portes:
            if getattr(p, "id", None) == door_id_int:
                porte_obj = p
                break

        if not porte_obj:
            print(f"[NET] Door {door_id} not found")
            return

        if state and not porte_obj.is_open:
            porte_obj.ouvrir()
        elif not state and porte_obj.is_open:
            porte_obj.fermer()

    def _update_remote_players(self, now):
        """
        Update remote player positions and remove inactive ones.

        Args:
            now: Current time.
        """
        for pid, data in list(self.remote_players.items()):
            node = data["node"]
            target = data.get("target_pos", node.getPos())
            cur = node.getPos()

            # Interpolate position
            node.setPos(cur + (target - cur) * 0.25)

            # Remove inactive players
            last_update = data.get("last_update", now)
            if now - last_update > self.CLIENT_TIMEOUT:
                print(f"[NET] Player timed out: {pid}")
                node.removeNode()
                del self.remote_players[pid]

    def send_door_toggle(self, door_id, state):
        """
        Send a door toggle message to the server.

        Args:
            door_id: The door ID.
            state: The new door state.
        """
        try:
            msg = json.dumps({
                "type": "door_toggle",
                "door_id": door_id,
                "state": state
            }).encode()
            self.sock.sendto(msg, self.server_addr)
        except Exception as e:
            print(f"[NET] Send door toggle error: {e}")

    def cleanup(self):
        """Clean up network resources."""
        if self.sock:
            self.sock.close()