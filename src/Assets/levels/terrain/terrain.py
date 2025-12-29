__license__ = "Regarder le fichier LICENSE.txt dans le répertoire racine du projet."
__author__ = "PFLIEGER-CHAKMA Nathan alias J0ytheC0de"

# --- Importations des modules Panda3D et Bullet ---
from panda3d.core import Vec4, NodePath, PointLight, CardMaker, TransparencyAttrib, Filename, Vec3, LPoint3f
from panda3d.bullet import BulletTriangleMesh, BulletTriangleMeshShape, BulletRigidBodyNode, BulletWorld
from Assets.utils import profile

from time import time

SHADOW_OFF = 0
SHADOW_LOW = 1
SHADOW_HIGH = 2


class Lamp:
    """Lampe compatible simplepbr optimisée (SpotLight unique)."""

    @profile
    def __init__(self, parent=None, lamp_node=None, color=(1, 1, 0.8, 1), 
                 height=-0.1, fov=170, near_far=(0.1, 20.0)):
        self.lamp_node = lamp_node
        self.parent = parent  # Terrain
        self.shadow_state = SHADOW_OFF

        # --- PLight unique ---
        self.light = PointLight(lamp_node.getName() + "_light")
        self.light.setColor(Vec4(*color))
        self.light.setShadowCaster(False)

        # --- NodePath ---
        self.light_np = self.parent.parent.render.attachNewNode(self.light)

        # --- Position et orientation ---
        self.light_np.setPos(self.lamp_node.getPos(self.parent.parent.render) + (0, 0, height))
        #self.light_np.lookAt(self.light_np.getPos(self.parent.parent.render) + (0, 0, -1))"""

    def update(self, player_pos, activation_distance=20.0):
        dist = (self.light_np.getPos(self.parent.parent.render) - player_pos).length()
        should_be_active = dist < activation_distance
        should_be_high = dist < activation_distance * 0.5

        # --- Gestion des shadows ---
        if not should_be_active:
            if self.shadow_state != SHADOW_OFF:
                self.light.setShadowCaster(False)
                self.shadow_state = SHADOW_OFF

        # --- Activation/désactivation réelle dans la scène ---
        if should_be_active:
            self.parent.parent.render.setLight(self.light_np)
        else:
            self.parent.parent.render.clearLight(self.light_np)




class Terrain:
    """Gère le modèle 3D du niveau, les collisions statiques et les éléments interactifs."""
    @profile
    def __init__(self, parent, model_path='Assets/levels/terrain/models/levelfun2.bam'):
        
        # Variables de gameplay (utilisées pour la propulsion du joueur)
        self.last_knockback_time = 0  # Temps du dernier recul
        self.knockback_cooldown = 0.5  # Temps minimum entre les reculs
        
        self.parent = parent # Référence à la classe App principale
        self.bullet_world = self.parent.bullet_world # Référence au monde physique Bullet
        
        # --- Chargement du modèle ---
        t0 = time()
        self.terrain = self.parent.loader.loadModel(model_path)
        print(f"[PROFILE] loadModel terrain: {time() - t0:.6f}s")
        self.terrain.reparentTo(self.parent.render)
        self.terrain.setTwoSided(False) # Rend l'intérieur invisible (optimisation)

        # Liste des objets Porte
        self.portes = []

        # --- Recherche des modèles de porte (NodePath) ---
        tporte1 = self.terrain.find("**/tdoor.001")
        tporte2 = self.terrain.find("**/tdoor.002")
        tporte3 = self.terrain.find("**/tdoor.003")
        tporte4 = self.terrain.find("**/tdoor.004")
        p1porte1 = self.terrain.find("**/tdoor.005")
        tgporte1 = self.terrain.find("**/tbigdoor.001")
        tgporte2 = self.terrain.find("**/tbigdoor.002")
        vent = self.terrain.find("**/grille_ventilation")
        
        # NOTE D'OPTIMISATION: C'est ici qu'il faut DÉTACHER ces NodePath 
        # (ex: tporte1.detachNode()) avant d'appeler flattenStrong pour éviter 
        # la double collision.

        # --- Création des objets Porte ---
        porte_definitions = [
            (tporte1, "gauche"), (tporte2, "gauche"), (tporte3, "spdroite"), 
            (tporte4, "gauche"), (p1porte1, "gauche"), (tgporte1, "droite"), 
            (tgporte2, "gauche"), (vent, "haut")
        ]

        for idx, (porte_np, sens) in enumerate(porte_definitions):
            if not porte_np.isEmpty():
                porte = Porte(
                    render=self.parent.render,
                    model_np=porte_np,
                    world=self.bullet_world,
                    excluded_materials=["Matériau.002"], # Matériaux à ignorer pour la collision de la porte
                    sens_ouverture=sens,
                    angle_ouverture=90,
                    vitesse=0.4
                )
                porte.id = idx  # <<=== ID UNIQUE pour la synchronisation réseau
                self.portes.append(porte)

        # --- Configuration des lampes ---
        self.lights = []

        # Trouver toutes les lampes par leur préfixe
        lampe_nodes = self.terrain.findAllMatches("**/lampe*") + self.terrain.findAllMatches("**/p1lampe*")

        for lamp_node in lampe_nodes:
            self._setup_light_for(lamp_node)
            lamp_node.setLightOff()  # Empêche le modèle de lampe d'être auto-éclairé

        # --- Optimisation de la scène ---
        # NOTE D'OPTIMISATION: Cet appel doit venir APRES avoir détaché toutes les portes.
        self.terrain.flattenStrong()

        # --- Génération de la collision statique ---
        # Exclut certains matériaux qui ne devraient pas avoir de collision (ex: verre, plantes).
        self.make_collision_from_model(self.terrain, self.bullet_world, ["Balloon3", "balloon1", "Balloon6.014", "glass", "matlight", "Matériau.003", "Matériau.006", "roof"])
        
        # NOTE D'OPTIMISATION: Si l'optimisation des tâches est faite, 
        self.parent.taskMgr.add(self.update, "terrain_update_task")

    @profile
    def make_collision_from_model(self, input_model, world, excluded_materials=None):
        """
        Crée une collision Bullet (BulletTriangleMeshShape) pour un modèle, 
        en parcourant les GeomNodes et en excluant par matériau.
        
        NOTE D'OPTIMISATION: Cette fonction est dupliquée dans Porte. 
        Elle devrait être factorisée dans une fonction utilitaire statique.
        """
        excluded_materials = excluded_materials or []
        mesh = BulletTriangleMesh()

        # Parcourt tous les GeomNodes du modèle
        for np in input_model.findAllMatches('**/+GeomNode'):
            geom_node = np.node()
            # Transformation nette pour positionner correctement la géométrie dans le mesh
            transform = np.getNetTransform().getMat()

            for i in range(geom_node.getNumGeoms()):
                state = geom_node.getGeomState(i)
                attrib = state.getAttrib(MaterialAttrib)
                mat_name = ""
                
                # Récupération du nom du matériau
                if attrib:
                    material = attrib.getMaterial()
                    if material:
                        mat_name = material.getName()

                # Exclusion par matériau (case-insensitive)
                if any(excl.lower() in mat_name.lower() for excl in excluded_materials):
                    continue

                # Ajout de la géométrie au mesh de collision
                geom = geom_node.getGeom(i)
                mesh.addGeom(geom, transform)

        if mesh.getNumTriangles() == 0:
            print("[TERRAIN] ⚠️ Aucun triangle de collision trouvé.")
            return None

        # Crée la forme et le corps Bullet
        tri_shape = BulletTriangleMeshShape(mesh, dynamic=False)
        body = BulletRigidBodyNode('terrain_collision')
        body.addShape(tri_shape)
        body.setMass(0) # Mass 0 = statique

        body_np = self.parent.render.attachNewNode(body)
        body_np.setCollideMask(BitMask32.allOn()) # Masque de collision actif
        world.attachRigidBody(body)
        return body_np

    def try_open_door(self):
        """Déclenche l'ouverture/fermeture de la porte la plus proche par le joueur."""
        player_pos = self.parent.player.controller_np.getPos(self.parent.render)
        nearest_door = None
        nearest_dist = 9999

        for porte in self.portes:
            # Vérifie si le corps physique existe
            if porte.body_np:
                door_pos = porte.body_np.getPos(self.parent.render)
                dist = (door_pos - player_pos).length()

                # Vérifie la proximité (rayon de 1 mètre)
                if dist < 1.0 and dist < nearest_dist: 
                    nearest_door = porte
                    nearest_dist = dist

        if nearest_door:
            nearest_door.toggle() # Ouvre/ferme la porte

            # --- SYNCHRONISATION RÉSEAU ---
            if hasattr(self.parent, "send_network"):
                # Envoie un paquet au serveur pour synchroniser l'état de la porte
                self.parent.send_network({
                    "type": "door_toggle",
                    "door_id": nearest_door.id,
                    "state": nearest_door.is_open # État final de la porte
                })
        else:
            print("[Terrain] Aucune porte proche à ouvrir.")

    def _setup_light_for(self, lamp_node: NodePath):
        """Crée une instance de Lamp et ajoute sa tâche d'update."""
        lamp = Lamp(parent=self, lamp_node=lamp_node)
        self.lights.append(lamp)

    def update(self, task):
        player_pos = self.parent.player.model.getPos(self.parent.render)

        for lamp in self.lights:
            lamp.update(player_pos)

        return task.cont


# --- Ré-importations spécifiques pour la classe Porte ---
# Panda3D Core (déjà importé en haut, mais redéfini ici pour la clarté du fichier original)
from panda3d.core import (
    BitMask32, NodePath, MaterialAttrib, Vec3
)
# Bullet (déjà importé en haut)
from panda3d.bullet import (
    BulletTriangleMesh, BulletTriangleMeshShape, BulletRigidBodyNode
)
from direct.interval.IntervalGlobal import Sequence, Parallel # Utile pour les animations (non utilisé ici, mais bonne pratique)


class Porte:
    """Gère un objet porte (modèle, collision physique et animation de rotation)."""
    def __init__(
        self,
        render,
        model_np,
        world,
        excluded_materials=None,
        dynamic=False,
        sens_ouverture="droite",
        angle_ouverture=90,
        vitesse=3.0,
        locked=False
    ):
        """
        Constructeur de la porte.
        :param model_np: NodePath du modèle de la porte (doit être détaché du terrain principal)
        """
        self.render = render
        self.model_np = model_np
        self.world = world
        self.excluded_materials = excluded_materials or []
        self.dynamic = dynamic
        self.sens_ouverture = sens_ouverture
        self.angle_ouverture = angle_ouverture
        self.vitesse = vitesse # Durée de l'animation en secondes
        self.locked = locked # Si la porte peut être ouverte ou non

        self.is_open = False
        self.id = -1 # Initialisation de l'ID réseau

        # Crée la collision Bullet pour la porte seule
        self.body_np = self._make_collision_from_model()

        # Attache le modèle visuel à l'objet physique
        if self.body_np:
            # On copie la transformation du modèle sur le body (déjà fait dans _make_collision_from_model, mais c'est une sécurité)
            self.body_np.setMat(self.model_np.getMat(self.render))

            # Reparentage : Le modèle visuel devient l'enfant du corps physique.
            # wrtReparentTo conserve la position et l'orientation globales du modèle.
            self.model_np.wrtReparentTo(self.body_np)
            
            # Le modèle est réinitialisé localement par rapport à son nouveau parent (le corps physique)
            self.model_np.setPos(0, 0, 0)
            self.model_np.setHpr(0, 0, 0)
            self.model_np.setScale(1, 1, 1)  # ✅ important : on remet l’échelle locale à 1

        # Stocke l'orientation de base (fermée)
        self.closed_hpr = self.model_np.getHpr()
        # Calcule l'orientation cible (ouverte)
        self.open_hpr = self._calc_open_hpr()

    # =====================================================
    # COLLISION
    # =====================================================
    @profile
    def _make_collision_from_model(self):
        """
        Crée la forme et le corps physique pour la porte.
        
        NOTE D'OPTIMISATION: Cette méthode est un doublon de Terrain.make_collision_from_model.
        Elle devrait être remplacée par un appel à la fonction utilitaire factorisée.
        """
        mesh = BulletTriangleMesh()
        
        # Parcourt les GeomNodes du modèle de porte
        for np in self.model_np.findAllMatches('**/+GeomNode'):
            geom_node = np.node()
            transform = np.getNetTransform().getMat()

            for i in range(geom_node.getNumGeoms()):
                state = geom_node.getGeomState(i)
                attrib = state.getAttrib(MaterialAttrib)
                mat_name = ""
                
                # ... Logique de vérification du matériau (identique à Terrain) ...
                if attrib:
                    material = attrib.getMaterial()
                    if material:
                        mat_name = material.getName()

                if any(excl.lower() in mat_name.lower() for excl in self.excluded_materials):
                    continue

                geom = geom_node.getGeom(i)
                mesh.addGeom(geom, transform)

        if mesh.getNumTriangles() == 0:
            print(f"[PORTE] ⚠️ Aucun triangle de collision pour {self.model_np.getName()}")
            return None

        tri_shape = BulletTriangleMeshShape(mesh, dynamic=self.dynamic)
        body = BulletRigidBodyNode(self.model_np.getName())
        # Tags pour interaction raycast
        body.setPythonTag("object", self)      # l’objet Porte
        body.setPythonTag("np", None)           # sera rempli juste après

        body.addShape(tri_shape)
        body.setMass(0 if not self.dynamic else 5) # Masse 0 pour une porte statique/animée

        # Crée le NodePath du corps Bullet et le place au bon endroit
        body_np = self.render.attachNewNode(body)
        body.setPythonTag("np", body_np)
        body_np.setTag("interactable", "1")    # tag panda (optionnel mais pratique)
        body_np.setPos(self.model_np.getPos(self.render))
        body_np.setHpr(self.model_np.getHpr(self.render))
        body_np.setScale(self.model_np.getScale(self.render))
        body_np.setCollideMask(BitMask32.bit(1)) # Masque de collision spécifique (bit 1)

        self.world.attachRigidBody(body)
        return body_np


    # =====================================================
    # ANIMATION
    # =====================================================
    def _calc_open_hpr(self):
        """Calcule la rotation finale (ouverte) selon le sens d’ouverture."""
        base_hpr = self.closed_hpr
        angle = self.angle_ouverture
        
        # Les rotations sont appliquées à l'axe H (Heading / Lacet)
        if self.sens_ouverture.lower() == "gauche":
            return base_hpr + (-angle, 0, 0)
        elif self.sens_ouverture.lower() == "droite":
            return base_hpr + (angle, 0, 0)
        # Les portes 'haut'/'bas' sont codées comme une rotation sur P ou R dans HPR (Pitch ou Roll),
        # mais ici elles utilisent H (pour des modèles peut-être modélisés différemment).
        elif self.sens_ouverture.lower() == "haut":
            return base_hpr + (0, 0, -angle)
        elif self.sens_ouverture.lower() == "bas":
            return base_hpr + (0, 0, angle)
        # ⚠️ Cas spécial: Rotation à 180 degrés
        elif self.sens_ouverture.lower() == "spdroite":
            return base_hpr + (-180, 0, 0)
        else:
            print(f"[PORTE] ⚠️ Sens inconnu '{self.sens_ouverture}', ouverture par défaut droite.")
            return base_hpr + (0, 0, angle)

    def ouvrir(self):
        """Déclenche l'animation d'ouverture."""
        if self.locked:
            return
        if not self.is_open:
            self.is_open = True
            # Animation de rotation de 'vitesse' secondes vers l'orientation ouverte
            self.body_np.hprInterval(self.vitesse, self.open_hpr).start()


    def fermer(self):
        """Déclenche l'animation de fermeture."""
        if self.is_open:
            # ⚠️ Logique non uniforme pour "spdroite"
            if not self.sens_ouverture.lower() == "spdroite":
                self.is_open = False
                # Fermeture normale : revient à l'orientation d'origine
                self.body_np.hprInterval(self.vitesse, self.closed_hpr).start()
            else:
                self.is_open = False
                # Fermeture spéciale : revient à closed_hpr - 90 degrés (HACK)
                # NOTE D'OPTIMISATION: Cela devrait être corrigé. La fermeture
                # devrait toujours revenir à self.closed_hpr. La modélisation
                # ou le calcul de closed_hpr est probablement erroné ici.
                self.body_np.hprInterval(self.vitesse, self.closed_hpr - (90, 0, 0)).start()


    def toggle(self):
        """Bascule l'état de la porte (ouvre si fermé, ferme si ouvert)."""
        if self.is_open:
            self.fermer()
        else:
            self.ouvrir()

    # =====================================================
    # OUTILS
    # =====================================================
    def set_open_angle(self, angle):
        """Met à jour l'angle d'ouverture et recalcule la HPR cible."""
        self.angle_ouverture = angle
        self.open_hpr = self._calc_open_hpr()

    def remove(self):
        """Nettoie et supprime la porte de la scène et du monde physique."""
        if self.body_np:
            self.world.removeRigidBody(self.body_np.node())
            self.body_np.removeNode()
        self.model_np.removeNode()