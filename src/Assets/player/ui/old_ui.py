#!/usr/bin/python
# -*- coding: utf-8 -*-

# This file was created using the DirectGUI Designer

__license__ = "la license ne s'applique pas à ce fichier"
__author__ = "PFLIEGER-CHAKMA Nathan alias J0ytheC0de"

from direct.gui import DirectGuiGlobals as DGG

from direct.gui.DirectFrame import DirectFrame
from direct.gui.DirectWaitBar import DirectWaitBar
from direct.gui.DirectLabel import DirectLabel
from panda3d.core import (
    LPoint3f,
    LVecBase3f,
    LVecBase4f,
    TextNode
)

class GUI:
    def __init__(self, rootParent=None):
        
        self.frame_for_bar = DirectFrame(
            frameSize = (0.0, 0.82, 0.0, 0.12),
            frameColor = (0.0, 1.0, 1.0, 0.2),
            pos = LPoint3f(0, 0, 0),
            parent=base.a2dBottomLeft,
        )
        self.frame_for_bar.setTransparency(0)

        self.hp_bar = DirectWaitBar(
            state = 'normal',
            frameSize = (0.0, 0.8, 0.0, 0.05),
            frameColor = (0.0, 0.9, 0.2, 1.0),
            pos = LPoint3f(0, 0, 0),
            text = '0%',
            text0_pos = (0.02, 0.01),
            text0_scale = (0.05, 0.05),
            text0_frame = LVecBase4f(0, 0.5, 0, 0.5),
            text0_align = 0,
            parent=self.frame_for_bar,
        )
        self.hp_bar.setTransparency(0)

        self.hp = DirectLabel(
            borderWidth = (0.0, 0.0),
            borderUvWidth = (0.0, 0.0),
            frameColor = (0.8, 0.8, 0.8, 0.0),
            pos = LPoint3f(0, 0, 0),
            scale = LVecBase3f(0.1, 0.1, 0.1),
            text = 'Label',
            text0_text = 'hp',
            text0_pos = (1.3, 0.05),
            text0_scale = (0.5, 0.5),
            text0_frame = LVecBase4f(1, 1, 1, 1),
            parent=self.hp_bar,
        )
        self.hp.setTransparency(0)

        self.stamina_bar = DirectWaitBar(
            state = 'normal',
            frameSize = (0.0, 0.8, 0.05, 0.1),
            frameColor = (0.0, 0.7, 0.9, 1.0),
            pos = LPoint3f(0, 0, 0),
            text = '0%',
            text0_pos = (0.053, 0.061),
            text0_scale = (0.05, 0.05),
            text0_frame = LVecBase4f(0, 0.5, 0, 0.5),
            parent=self.frame_for_bar,
        )
        self.stamina_bar.setTransparency(0)

        self.stamina = DirectLabel(
            frameColor = (0.8, 0.8, 0.8, 0.0),
            pos = LPoint3f(0, 0, 0),
            scale = LVecBase3f(0.1, 0.1, 0.1),
            text = 'Label',
            text0_text = 'Stamina',
            text0_pos = (1.9, 0.6),
            text0_scale = (0.5, 0.5),
            parent=self.stamina_bar,
        )
        self.stamina.setTransparency(0)

        self.weapon_info = DirectFrame(
            frameSize = (-0.61, -0.2, 0.0, 0.21),
            frameColor = [1.0, 1.0, 1.0, 0.2],
            pos = LPoint3f(0, 0, 0),
            parent=base.a2dBottomRight,
        )
        self.weapon_info.setTransparency(0)

        self.ball_out = DirectLabel(
            relief = 0,
            frameSize = (-4.0, -6.0, 0.0, 2.0),
            pos = LPoint3f(0, 0, 0),
            scale = LVecBase3f(0.1, 0.1, 0.1),
            text = 'Label',
            text0_text = '0',
            text0_pos = (-5.1, 0.75),
            parent=self.weapon_info,
        )
        self.ball_out.setTransparency(0)

        self.ball_in = DirectLabel(
            relief = 0,
            frameSize = (-4.0, -2.0, 0.0, 2.0),
            pos = LPoint3f(0, 0, 0),
            scale = LVecBase3f(0.1, 0.1, 0.1),
            text = 'Label',
            text0_text = '0',
            text0_pos = (-3.1, 0.75),
            parent=self.weapon_info,
        )
        self.ball_in.setTransparency(0)


    def show(self):
        self.frame_for_bar.show()
        self.weapon_info.show()

    def hide(self):
        self.frame_for_bar.hide()
        self.weapon_info.hide()

    def destroy(self):
        self.frame_for_bar.destroy()
        self.weapon_info.destroy()
