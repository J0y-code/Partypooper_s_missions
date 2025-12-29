__license__ = "Regarder le fichier LICENSE.txt dans le répertoire racine du projet."
__author__ = "PFLIEGER-CHAKMA Nathan alias J0ytheC0de"

from panda3d.bullet import BulletCapsuleShape, BulletCharacterControllerNode, ZUp
from direct.task import Task
from panda3d.core import KeyboardButton, Vec3
from direct.showbase.ShowBaseGlobal import globalClock

from .ui.player_gui import GUI
from .Character import Character
from .player_raycast import PlayerRaycast

from time import sleep

# Import pour __main__ seulement
if __name__ == '__main__':
    from direct.showbase.ShowBase import ShowBase

class Player:
    #  Constantes de configuration 
    DEFAULT_RUN_SPEED = 3.0
    DEFAULT_WALK_SPEED = 1.5
    CROUCH_RUN_SPEED = 0.5
    CROUCH_WALK_SPEED = 0.1
    STAMINA_LOW_THRESHOLD = 20
    STAMINA_CRITICAL_THRESHOLD = 10
    TELEPORT_HEIGHT = -50
    TELEPORT_TARGET_Z = 200
    SENSIBILITY = 0.1
    FOV = 120
    JUMP_HEIGHT = 0.5
    JUMP_SPEED = 4.0
    STAMINA_DRAIN_RATE = 2.5
    STAMINA_REGEN_STILL = 7.5
    STAMINA_REGEN_MOVING = 5.0
    CAMERA_SHAKE_INTENSITY_MULTIPLIER = 0.005
    MODEL_HEIGHT_OFFSET = 1.773 / 2
    CROUCH_MODEL_Z = -1.8
    CROUCH_CONTROLLER_Z_OFFSET = -0.4
    STAND_MODEL_Z = -1.773 / 2

    def __init__(self, parentClass=None, model='models/playertest.bam'):
        """
        Initialise le joueur avec ses paramètres et composants.

        Args:
            parentClass: L'instance principale de l'application (ShowBase).
            model: Chemin vers le modèle du joueur.
        """
        #  état 
        self.parentClass = parentClass
        self.ui = GUI()
        self.knockback_vector = Vec3(0, 0, 0)
        self.knockback_time = 0.0


        self.iscrounching = False
        self.dead_state = False
        self.camera_up = False


        #  paramètres mouvement / caméra 
        self.runspeed = self.DEFAULT_RUN_SPEED
        self.walkspeed = self.DEFAULT_WALK_SPEED
        self.stamina = 100
        self.hp = 100
        self.flou = 1
        self.sensibility = max(0.01, self.SENSIBILITY)  # Validation pour éviter 0
        self.mouse_center = (self.parentClass.win.getXSize() // 2, self.parentClass.win.getYSize() // 2)
        self.jumping = False


        #  Bullet world 
        self.bullet_world = self.parentClass.bullet_world
        self.bullet_world.setGravity(Vec3(0, 0, -9.81))


        #  formes (debout / accroupi) 
        self.shape = BulletCapsuleShape(0.4/2, 1.773 - 2*0.4/2, ZUp)   # debout


        #  character controller (une seule création ici) 
        self.controller = BulletCharacterControllerNode(self.shape, 0.4, 'Player')
        self.controller_np = self.parentClass.render.attachNewNode(self.controller)
        self.controller_np.setPos(0, 0, 1)
        self.bullet_world.attachCharacter(self.controller)


        #  modèle visuel (après création du controller) 
        self.character = Character(self.parentClass)
        self.model = self.character.actor
        self.model.reparentTo(self.controller_np)
        self.model.setH(0)
        self.model.setZ(0 - 1.773/2)  # ajuster la hauteur du modèle par rapport au controller


        #  caméra 
        self.head_np = self.model.exposeJoint(None, "modelRoot", "mixamorig:Head")


        # Node intermédiaire pour corriger le roll
        self.camera_roll_correction = self.head_np.attachNewNode("camera_roll_correction")
        self.camera_roll_correction.setHpr(0, 0, 0)  # Roll, pitch, yaw neutres
        self.camera_z = 10
        self.camera_roll_correction.setPos(-10, -15, self.camera_z)  # recul + hauteur caméra


        # Lens
        self.parentClass.camLens.setFov(120)
        self.parentClass.camLens.setNearFar(0.1, 150)


        #  contrôle du cou 
        self.neck_np = self.model.controlJoint(None, "modelRoot", "mixamorig:Neck")
        self.neck_np.setR(0)  # verrouiller le roll sur le cou


        self.turning = False  # état de rotation forcée
        self.moving = False  # état de mouvement forcé


        self.raycast = PlayerRaycast(
            render=self.parentClass.render,
            camera=self.parentClass.camera,
            bullet_world=self.parentClass.bullet_world,
            max_distance=2.5,
        )


        #  input 
        self.controls = {
            "z": "forward",
            "s": "backward",
            "q": "left",
            "d": "right",
            "c": "crouch",
            "shift": "run",
            "space": "jump"
        }
        self.parentClass.accept("e", self.try_interact)
        self.parentClass.accept("e-repeat", self.try_interact)

        self.parentClass.keyMap = {action: False for action in self.controls.values()}
        for key, action in self.controls.items():
            self.parentClass.accept(key, self.setKey, [action, True])
            self.parentClass.accept(f"{key}-up", self.setKey, [action, False])

        #  HUD / lastpos / filters 
        self.lastpos = self.controller_np.getPos()
        self.fov = 120

        #  tasks 
        self.parentClass.taskMgr.add(self.update_player, "update_player")
        self.parentClass.taskMgr.add(self.param_stamina, "param_stamina")
        self.parentClass.taskMgr.add(self.update_camera, "update_camera")
        # à la fin du __init__
        self.parentClass.taskMgr.doMethodLater(0.1, self.init_filters, "init_filters")
        self.parentClass.taskMgr.add(self.raycast.update_debug_smoothly, "update_raycast_debug")

    def try_interact(self):
        """Tente une interaction avec l'environnement via le raycast."""
        if self.raycast.interact():
            print("[Player: Raycast] Interaction réussie")
        else:
            print("[Player: Raycast] Rien à interagir")

    def setKey(self, key, value):
        """Met à jour l'état d'une touche dans keyMap."""
        self.parentClass.keyMap[key] = value

    def jump(self):
        """Fait sauter le joueur si possible."""
        if not self.jumping and self.controller.isOnGround():
            self.controller.setMaxJumpHeight(self.JUMP_HEIGHT)
            self.controller.setJumpSpeed(self.JUMP_SPEED)
            self.controller.doJump()
            self.jumping = True

    def update_player(self, task):
        dt = globalClock.getDt()
        mw = self.parentClass.mouseWatcherNode

        # Gestion de la mort
        self.handle_death()

        # Téléport si tombé
        self.handle_teleport()

        # Knockback
        if self.handle_knockback(dt):
            return Task.cont

        # Input mouvement et animations
        input_vector = self.handle_movement_input(mw)

        # Crouch
        self.handle_crouch(mw)

        # Jump
        self.handle_jump(mw)

        # Calcul et application du mouvement
        self.apply_movement(input_vector, mw, dt)

        return Task.cont

    def handle_death(self):
        """Gère la logique de mort du joueur."""
        if self.hp <= 0 and not self.dead_state:
            if hasattr(self.parentClass, 'terrain') and hasattr(self.parentClass.terrain, "batterie_3d"):
                musique = self.parentClass.terrain.batterie_3d
                new_time = max(0, musique.getTime() - 0.4)
                self.dead_state = True
                for i in range(20):
                    musique.setTime(new_time)
                    musique.play()
                    sleep(0.3)
                self.parentClass.quit_game()
            else:
                print("[Player] Erreur : musique non disponible, arrêt du jeu.")
                self.parentClass.quit_game()

    def handle_teleport(self):
        """Téléporte le joueur s'il est tombé trop bas."""
        if self.controller_np.getZ() < self.TELEPORT_HEIGHT:
            target_pos = Vec3(self.controller_np.getX(), self.controller_np.getY(), self.TELEPORT_TARGET_Z)
            h, p, r = self.controller_np.getH(), self.controller_np.getP(), self.controller_np.getR()

            try:
                self.bullet_world.removeCharacter(self.controller)
            except Exception as e:
                print(f"[Player] Erreur lors de la suppression du controller : {e}")

            self.controller_np.setPos(target_pos)
            self.controller_np.setHpr(h, p, r)
            self.bullet_world.attachCharacter(self.controller)

            try:
                self.controller.setLinearMovement(Vec3(0, 0, 0), True)
            except Exception as e:
                print(f"[Player] Erreur lors de l'arrêt du mouvement : {e}")

    def handle_knockback(self, dt):
        """Gère le knockback. Retourne True si knockback actif."""
        if self.knockback_time > 0:
            self.controller.setLinearMovement(self.knockback_vector, True)
            self.knockback_time -= dt
            return True
        return False

    def handle_movement_input(self, mw):
        """Gère les inputs de mouvement et met à jour les animations."""
        input_vector = Vec3(0, 0, 0)

        if mw.is_button_down(KeyboardButton.ascii_key("z")):
            input_vector.y += 1
        if mw.is_button_down(KeyboardButton.ascii_key("s")):
            input_vector.y -= 1
        if mw.is_button_down(KeyboardButton.ascii_key("q")):
            input_vector.x -= 1
        if mw.is_button_down(KeyboardButton.ascii_key("d")):
            input_vector.x += 1

        if input_vector.length_squared() > 0:
            if mw.is_button_down(KeyboardButton.lshift()) and self.stamina > 0:
                if self.character.state != 'Run':
                    self.character.request('Run')
            else:
                if self.character.state != 'Walk':
                    self.character.request('Walk')
            self.moving = True
        else:
            if self.character.state != 'Idle':
                self.character.request('Idle')
            self.moving = False

        return input_vector

    def handle_crouch(self, mw):
        """Gère l'accroupissement."""
        if mw.is_button_down(KeyboardButton.ascii_key("c")):
            if not self.iscrounching and not self.jumping:
                self._switch_to_crouch()
        else:
            if self.iscrounching:
                self._switch_to_stand()

    def _switch_to_crouch(self):
        """Passe en mode accroupi en changeant la forme du controller."""
        if not self.iscrounching:
            sz = 0.6
            self.controller.getShape().setScale(Vec3(1, 1, sz))
            self.controller_np.setScale(Vec3(1, 1, sz))
            self.controller_np.setZ(self.controller_np.getZ() - 0.4)
            self.model.setZ(self.CROUCH_MODEL_Z)
            self.runspeed = self.CROUCH_RUN_SPEED
            self.walkspeed = self.CROUCH_WALK_SPEED
            self.iscrounching = True

    def _switch_to_stand(self):
        """Passe en mode debout en changeant la forme du controller."""
        if self.iscrounching:
            sz = 1.0
            self.controller.getShape().setScale(Vec3(1, 1, sz))
            self.controller_np.setScale(Vec3(1, 1, sz))
            self.controller_np.setZ(self.controller_np.getZ() + 0.4)
            self.model.setZ(self.STAND_MODEL_Z)
            self.runspeed = self.DEFAULT_RUN_SPEED
            self.walkspeed = self.DEFAULT_WALK_SPEED
            self.iscrounching = False

    def handle_jump(self, mw):
        """Gère le saut."""
        if mw.is_button_down(KeyboardButton.space()):
            self.jump()
        if self.controller.isOnGround():
            self.jumping = False

    def apply_movement(self, input_vector, mw, dt):
        """Calcule et applique le mouvement."""
        speed = self.runspeed if mw.is_button_down(KeyboardButton.lshift()) else self.walkspeed

        if input_vector.length_squared() > 0:
            input_vector.normalize()
            input_vector *= speed
            input_vector = self.model.getQuat(self.parentClass.render).xform(input_vector)

        try:
            self.controller.setLinearMovement(input_vector, True)
        except Exception:
            self.controller_np.setPos(self.controller_np.getPos() + input_vector * dt)

    def param_stamina(self, task):
        """
        Met à jour la stamina, ajuste les vitesses, applique le shake caméra et met à jour l'UI.
        """
        dt = globalClock.getDt()
        mw = self.parentClass.mouseWatcherNode

        #  Calcul déplacement 
        current_pos = self.controller_np.getPos()
        move_speed = (current_pos - self.lastpos).length() / max(dt, 1e-6)
        self.lastpos = current_pos

        #  RÉDUCTION / regen STAMINA 
        if mw.is_button_down(KeyboardButton.lshift()) and move_speed > 0:
            self.stamina = max(0, self.stamina - self.STAMINA_DRAIN_RATE * dt)
        else:
            regen = self.STAMINA_REGEN_STILL if move_speed == 0 else self.STAMINA_REGEN_MOVING
            self.stamina = min(100, self.stamina + regen * dt)

        #  AJUSTEMENT VITESSE 
        if self.stamina < self.STAMINA_LOW_THRESHOLD:
            self.runspeed = 1
            self.walkspeed = 0.833
        else:
            self.runspeed = self.DEFAULT_RUN_SPEED
            self.walkspeed = self.DEFAULT_WALK_SPEED

        #  SHAKE CAM SI PEU DE STAMINA 
        if self.stamina < self.STAMINA_CRITICAL_THRESHOLD:
            shake_intensity = (self.STAMINA_CRITICAL_THRESHOLD - self.stamina) * self.CAMERA_SHAKE_INTENSITY_MULTIPLIER
            self.parentClass.camera.setX(
                self.parentClass.camera,
                shake_intensity * (-1 if globalClock.getFrameCount() % 2 == 0 else 1),
            )

        #  MISE À JOUR BARRES UI 
        stamina_ratio = self.stamina / 100
        self.ui.stamina_bar['frameSize'] = (0.0, 0.8 * stamina_ratio, 0.05, 0.1)
        self.ui.stamina_bar['text'] = f"{int(self.stamina)}%"

        if hasattr(self, 'hp'):
            hp_ratio = self.hp / 100
            self.ui.hp_bar['frameSize'] = (0.0, 0.8 * hp_ratio, 0.0, 0.05)
            self.ui.hp_bar['text'] = f"{int(self.hp)}%"

        return Task.cont

    def update_camera(self, task):
        dt = globalClock.getDt()

        if self.parentClass.mouseWatcherNode.hasMouse():
            md = self.parentClass.win.getPointer(0)
            x, y = md.getX(), md.getY()
            self.parentClass.win.movePointer(0, *self.mouse_center)

            dx = (self.mouse_center[0] - x) * self.sensibility
            dy = (self.mouse_center[1] - y) * self.sensibility

            #  INPUT SUR LE COU (LOCAL AU CORPS) 
            self.neck_np.setH(self.neck_np.getH() + dx)

            new_pitch = self.neck_np.getP() - dy
            self.neck_np.setP(max(-75, min(60, new_pitch)))

        # ===== DIFF COU / CORPS (LOCAL !) =====
        diff = self.neck_np.getH()

        max_angle = 15
        follow_speed = 30
        max_turn_speed = 360  # deg/s

        if abs(diff) > max_angle:
            # quantité à rattraper
            excess = diff - max_angle if diff > 0 else diff + max_angle

            turn = excess * follow_speed * dt
            turn = max(-max_turn_speed * dt, min(max_turn_speed * dt, turn))

            #  le corps tourne 
            self.model.setH(self.model, turn)

            #  le cou garde une rotation cohérente 
            self.neck_np.setH(diff - turn)

        if abs(diff) > 180:
            corrige_turn = self.neck_np.getH()
            self.model.setH(corrige_turn)

        # ===== CAMÉRA =====
        cam_pos = self.camera_roll_correction.getPos(self.parentClass.render)
        cam_h = self.camera_roll_correction.getH(self.parentClass.render) + 157.5
        cam_p = -self.camera_roll_correction.getP(self.parentClass.render)

        self.parentClass.camera.setPos(cam_pos)
        self.parentClass.camera.setHpr(cam_h, cam_p, 0)
        if self.moving:
            #self.model.setH(render, self.parentClass.camera.getH())
            pass

        return Task.cont


    def init_filters(self, task):
        if self.parentClass.camNode and self.parentClass.camNode.getDisplayRegion(0):
            #self.filters = CommonFilters(self.parentClass.win, self.parentClass.cam)
            #self.filters.setBlurSharpen(1)
            return Task.done
        else:
            print("⚠️ Caméra non encore prête, filtres désactivés.")
            self.filters = None
            return Task.cont

if __name__ == '__main__':
    app = ShowBase()
    player = Player(parentClass=app)
    app.run()
