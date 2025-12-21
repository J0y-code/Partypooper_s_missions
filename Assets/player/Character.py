__license__ = "Regarder le fichier LICENSE.txt dans le répertoire racine du projet."
__author__ = "PFLIEGER-CHAKMA Nathan alias J0ytheC0de"

from direct.actor.Actor import Actor
from direct.fsm.FSM import FSM

class Character(FSM):
    def __init__(self, parent):
        FSM.__init__(self, 'AvatarFSM')
        self.parent = parent

        # Chargement des modèles / animations
        if __name__ == "__main__":
            self.actor = Actor(
                "..\\player\\models\\partypooper.bam",
                {
                    "walk": "..\\player\\models\\animation\\walk.bam",
                    "run": "..\\player\\models\\animation\\run.bam",
                    "idle": "..\\player\\models\\animation\\idle.bam",
                    "idle2walk": "..\\player\\models\\animation\\idle2walk.bam",
                }
            )
        else:
            self.actor = Actor(
                "Assets\\player\\models\\partypooper.bam",
                {
                    "walk": "Assets\\player\\models\\animation\\walk.bam",
                    "run": "Assets\\player\\models\\animation\\run.bam",
                    "idle": "Assets\\player\\models\\animation\\idle.bam",
                    "idle2walk": "Assets\\player\\models\\animation\\idle2walk.bam",
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
