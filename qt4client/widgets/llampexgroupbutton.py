#!/usr/bin/env python

from PyQt4 import QtCore, QtGui
import math, sys, random
import os, os.path
def filepath(): return os.path.abspath(os.path.dirname(__file__))
def filedir(x): # convierte una ruta relativa a este fichero en absoluta
    if os.path.isabs(x): return x
    else: return os.path.join(filepath(),x)
    

class LlampexActionButton(QtGui.QToolButton):
    def __init__(self, text, key, icon, fn = None, parent=None):
        super(LlampexActionButton, self).__init__(parent)
        self._key = key
        self._callback = fn
        self.connect(self,QtCore.SIGNAL("clicked()"),self.button_clicked)
        self.setAutoRaise(True)
        self.setText(text)
        if icon:
            self.setIcon(icon)
        self.setIconSize(QtCore.QSize(32,32))
        self.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)
        #self.setSizePolicy(QtGui.QSizePolicy.Expanding,QtGui.QSizePolicy.Fixed)
        self.setSizePolicy(QtGui.QSizePolicy.Preferred,QtGui.QSizePolicy.Preferred)
        self.setMinimumWidth(64)
        self.setMaximumWidth(256)
        self.setMinimumHeight(40)
        self.setMaximumHeight(40)
        
    def button_clicked(self):
        if self._callback:
            self._callback(self._key)
        else:
            print "Clicked", self._key
    
class LlampexGroupButton(QtGui.QGroupBox):
    def __init__(self, text = "ActionGroup", parent=None):
        super(LlampexGroupButton, self).__init__(text,parent)
        self.layout = QtGui.QGridLayout()
        self.setLayout(self.layout)
        self.setSizePolicy(QtGui.QSizePolicy.Expanding,QtGui.QSizePolicy.Preferred)
        

        self.ncontrol = 0
        self.controlwidth = 3
    
    def addAction(self, text, key, icon, fn = None):
        x = int(self.ncontrol % self.controlwidth)
        y = int((self.ncontrol - x) / self.controlwidth)
        button = LlampexActionButton(text, key, icon, fn)
        self.ncontrol +=1
        self.layout.addWidget(button,y,x)
        
    def addSeparator(self,sz = 16):
    
        while int(self.ncontrol % self.controlwidth) >0: 
            self.ncontrol += 1
        x = int(self.ncontrol % self.controlwidth)
        y = int((self.ncontrol - x) / self.controlwidth)
        
        spacer = QtGui.QSpacerItem(sz,sz)
        self.layout.addItem(spacer,y,x,1,self.controlwidth )
        self.ncontrol += self.controlwidth
        
        
        
    
