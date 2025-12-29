#!/usr/bin/python
# -*- coding: utf-8 -*-

from direct.gui.DirectGui import (
    DirectButton, DirectFrame, DirectLabel, DirectEntry
)
from panda3d.core import TextNode, LPoint3f, LVecBase3f, LVecBase4f


class Menu:

    def __init__(self, parent=None, start_callback=None):
        self.parent = parent
        self.start_callback = start_callback
        self.widgets = []

        # ------------------------------
        # STORY FRAME (cachée au début)
        # ------------------------------
        self.Storyframe = DirectFrame(
            frameSize=(-0.3, 1.3, -0.97, 0.97),
            frameColor=(0.0, 0.0, 0.5, 0.8),
            pos=(0, 0, 0),
            image="Assets/main_ui/story.png",
            image_scale=(0.7, 1, 0.8),
            image_pos=(0.525, 0, 0),
        )
        self.Storyframe.setTransparency(True)
        self.Storyframe.hide()
        self.widgets.append(self.Storyframe)

        self.close_story_btn = DirectButton(
            parent=self.Storyframe,
            text="X",
            scale=0.1,
            pos=(1.23, 0, 0.87),
            frameColor=(0.8, 0.2, 0.2, 1.0),
            command=self.hide_storyframe,
        )
        self.widgets.append(self.close_story_btn)

        # ------------------------------
        # LEFT SIDEBAR
        # ------------------------------
        self.left_sidebar = DirectFrame(
            frameSize=(0.0, 1.0, -1.0, 1.0),
            frameColor=(0, 0, 0, 0.99),
            pos=(0, 0, 0),
            parent=base.a2dLeftCenter,
        )
        self.widgets.append(self.left_sidebar)

        # ------------------------------
        # TITLE
        # ------------------------------
        # --- Titre principal
        self.Title = DirectLabel(
            frameColor = (0.8, 0.8, 0.8, 0.0),
            pos = LPoint3f(0, 0, 0),
            scale = LVecBase3f(0.1, 0.1, 0.1),
            text = 'Label',
            text0_text = "Partypooper's Missions",
            text0_pos = (5.0, 8.0),
            text0_scale = (0.8, 1.0),
            text0_fg = LVecBase4f(0, 0, 1, 1),
            parent=self.left_sidebar,
        )
        self.Title.setTransparency(0)

        self.Titleliminal = DirectLabel(
            frameColor = (0.8, 0.8, 0.0, 0.2),
            pos = LPoint3f(0.5, 0, 0.9),
            scale = LVecBase3f(0.1, 0.1, 0.1),
            text = 'Label',
            text0_text = 'The Backrooms',
            text0_fg = LVecBase4f(1, 1, 0, 1),
            parent=self.left_sidebar,
        )

        # --- Cadre des boutons
        self.Buttonframe = DirectFrame(
            frameSize=(0.05, 0.95, -0.95, 0.7),
            frameColor=(0.01, 0.01, 0.01, 0.99),
            pos=LPoint3f(0, 0, 0),
            parent=self.left_sidebar,
        )

        self.Startbtn = DirectButton(
            relief = 1,
            frameColor = (0.2, 0.2, 0.2, 1.0),
            frameVisibleScale = (2.275, 2.0),
            pos = LPoint3f(0.375, 0, 0.575),
            scale = LVecBase3f(0.1, 0.1, 0.1),
            text = 'button',
            text0_text = 'Jouer',
            text1_text = 'Chargement...',
            text2_text = 'Jouer?',
            text3_text = 'chargement...',
            parent=self.Buttonframe,
            pressEffect=1,
            command=self.show_play_menu,
        )
        self.Startbtn.setTransparency(0)

        self.Storybtn = DirectButton(
            relief = 1,
            frameColor = (0.2, 0.2, 0.2, 1.0),
            frameVisibleScale = (1.75, 2.0),
            pos = LPoint3f(0.375, 0, 0.4),
            scale = LVecBase3f(0.1, 0.1, 0.1),
            text = 'button',
            text0_text = 'Histoire',
            text1_text = 'Raconte...',
            text2_text = 'Raconter?',
            parent=self.Buttonframe,
            pressEffect=1,
            command=self.show_storyframe,
        )
        self.widgets.append(self.Storybtn)

        # ------------------------------------------------------------
        # MENU SOLO / MULTI (caché au début)
        # ------------------------------------------------------------
        self.play_menu = DirectFrame(
            frameColor=(0, 0, 0, 0.8),
            frameSize=(-0.4, 0.4, -0.5, 0.5),
            pos=(0.375, 0, 0.1),
        )
        self.play_menu.hide()
        self.widgets.append(self.play_menu)

        self.play_label = DirectLabel(
            parent=self.play_menu,
            text="Choisir un mode",
            scale=0.07,
            pos=(0, 0, 0.35),
            frameColor=(0, 0, 0, 0)
        )

        # SOLO
        self.solo_btn = DirectButton(
            parent=self.play_menu,
            text="Solo",
            pos = LPoint3f(-0.1, 0, 0),
            scale = LVecBase3f(0.1, 0.1, 0.1),
            frameColor=(0.2, 0.2, 0.2, 1),
            command=lambda: self.start_callback("solo")
        )

        # MULTI
        self.multi_btn = DirectButton(
            parent=self.play_menu,
            text="Multijoueur",
            pos = LPoint3f(-0.1, 0, -0.15),
            scale = LVecBase3f(0.1, 0.1, 0.1),
            frameColor=(0.2, 0.2, 0.2, 1),
            command=self.show_multi_menu
        )

        # ------------------------------------------------------------
        # MENU MULTI (IP + Port)
        # ------------------------------------------------------------
        self.multi_menu = DirectFrame(
            parent=self.play_menu,
            frameColor=(0, 0, 0, 0.8),
            frameSize=(-0.45, 0.45, -0.6, 0.6),
            pos=(0, 0, 0),
        )
        self.multi_menu.hide()
        self.widgets.append(self.multi_menu)

        DirectLabel(
            parent=self.multi_menu,
            text="Connexion réseau",
            scale=0.07,
            pos=(0, 0, 0.4),
            frameColor=(0, 0, 0, 0)
        )

        DirectLabel(
            parent=self.multi_menu,
            text="IP du serveur :",
            scale=0.05,
            pos=(0, 0, 0.2),
            frameColor=(0, 0, 0, 0)
        )
        self.ip_entry = DirectEntry(
            parent=self.multi_menu,
            scale=0.05,
            pos=(-0.35, 0, 0.12),
            width=20,
            initialText="127.0.0.1",
            numLines=1
        )

        DirectLabel(
            parent=self.multi_menu,
            text="Port :",
            scale=0.05,
            pos=(0, 0, -0.05),
            frameColor=(0, 0, 0, 0)
        )
        self.port_entry = DirectEntry(
            parent=self.multi_menu,
            scale=0.05,
            pos=(-0.35, 0, -0.13),
            width=20,
            initialText="8080",
            numLines=1
        )

        self.join_btn = DirectButton(
            parent=self.multi_menu,
            text="Rejoindre",
            scale=0.06,
            pos=(0, 0, -0.35),
            frameColor=(0.2, 0.2, 0.2, 1),
            command=self.connect_multiplayer
        )

        # ----------------------------------------------------------------------
        # Dans le menu play_menu, ajouter un bouton retour vers le menu principal
        # ----------------------------------------------------------------------
        self.play_back_btn = DirectButton(
            parent=self.play_menu,
            text="Retour",
            pos=LPoint3f(0, 0, -0.35),
            scale=LVecBase3f(0.07, 0.07, 0.07),
            frameColor=(0.8, 0.2, 0.2, 1),
            command=lambda: self.play_menu.hide()
        )
        self.widgets.append(self.play_back_btn)

        # ----------------------------------------------------------------------
        # Dans le menu multi_menu, ajouter un bouton retour vers le menu play_menu
        # ----------------------------------------------------------------------
        self.multi_back_btn = DirectButton(
            parent=self.multi_menu,
            text="Retour",
            pos=LPoint3f(0, 0, -0.45),
            scale=LVecBase3f(0.07, 0.07, 0.07),
            frameColor=(0.8, 0.2, 0.2, 1),
            command=self.show_play_menu
        )
        self.widgets.append(self.multi_back_btn)


    # ----------------------------------------------------------------------
    # Show menus
    # ----------------------------------------------------------------------
    def show_play_menu(self):
        self.play_menu.show()
        self.play_label.show()
        self.solo_btn.show()
        self.multi_btn.show()
        self.play_back_btn.show()
        self.multi_menu.hide()

    def show_multi_menu(self):
        self.multi_menu.show()
        self.play_label.hide()
        self.solo_btn.hide()
        self.multi_btn.hide()
        self.play_back_btn.hide()
        self.multi_back_btn.show()



    # ----------------------------------------------------------------------
    # Handle multiplayer connection
    # ----------------------------------------------------------------------
    def connect_multiplayer(self):
        ip = self.ip_entry.get().strip()
        port = int(self.port_entry.get().strip())

        if self.start_callback:
            self.start_callback("multi", ip, port)

    # ----------------------------------------------------------------------
    # Story menu
    # ----------------------------------------------------------------------
    def show_storyframe(self):
        self.Storyframe.show()

    def hide_storyframe(self):
        self.Storyframe.hide()

    # ----------------------------------------------------------------------
    def show(self):
        for w in self.widgets:
            w.show()

    def hide(self):
        for w in self.widgets:
            w.hide()

    def destroy(self):
        for w in self.widgets:
            w.destroy()
