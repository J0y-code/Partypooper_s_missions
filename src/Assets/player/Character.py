__license__ = "Regarder le fichier LICENSE.txt dans le répertoire racine du projet."
__author__ = "PFLIEGER-CHAKMA Nathan alias J0ytheC0de"

from direct.actor.Actor import Actor
from direct.fsm.FSM import FSM
import os


class Character(FSM):
    def __init__(self, parent):
        FSM.__init__(self, 'AvatarFSM')
        self.parent = parent

        # Determine asset paths
        if __name__ == "__main__":
            base_path = os.path.join("..", "player", "models")
        else:
            base_path = "Assets/player/models"

        # Load model and animations
        self.actor = Actor(
            os.path.join(base_path, "partypooper.bam"),
            {
                "walk": os.path.join(base_path, "animation", "walk.bam"),
                "run": os.path.join(base_path, "animation", "run.bam"),
                "idle": os.path.join(base_path, "animation", "idle.bam"),
                "idle2walk": os.path.join(base_path, "animation", "idle2walk.bam"),
            }
        )
        
        # Parenting
        try:
            self.actor.reparentTo(self.parent.parent.render)
        except:
            self.actor.reparentTo(self.parent.render)

        # 🔹 Contrôler uniquement le cou pour bloquer le roll
        self.neck_np = self.actor.controlJoint(None, "modelRoot", "mixamorig:Neck")
        self.neck_np.setR(0)  # verrouillage du roll

    # --- FSM ---
    def enterWalk(self):
        if self.state != 'Walk':
            self.actor.play('idle2walk')
            self.actor.loop('walk')

    def exitWalk(self):
        self.actor.stop()

    def enterRun(self):
        self.actor.loop('run')

    def exitRun(self):
        self.actor.stop()

    def enterIdle(self):
        self.actor.loop('idle')

    def exitIdle(self):
        self.actor.stop()


if __name__ == "__main__":
    from direct.showbase.ShowBase import ShowBase

    class MyApp(ShowBase):
        def __init__(self):
            ShowBase.__init__(self)
            self.character = Character(self)
            self.character.request('Idle')
            self.character.actor.setZ(0-1.65/2)

            # Vérifier le contrôle du cou
            print("Joints contrôlés :")
            for joint in self.character.actor.getJoints():
                print(joint)

    app = MyApp()
    app.run()
