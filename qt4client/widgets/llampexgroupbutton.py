#!/usr/bin/env python

from PyQt4 import QtCore, QtGui
import math, sys, random
import os, os.path
def filepath(): return os.path.abspath(os.path.dirname(__file__))
def filedir(x): # convierte una ruta relativa a este fichero en absoluta
    if os.path.isabs(x): return x
    else: return os.path.join(filepath(),x)
    
MIN_DRAG_DISTANCE = 16

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
        self.dragStartPoint = None
        
    def button_clicked(self):
        if self._callback:
            self._callback(self._key)
        else:
            print "Clicked", self._key
            
    def mouseMoveEvent(self, e):
        QtGui.QToolButton.mouseMoveEvent(self, e)
        if e.buttons() == QtCore.Qt.LeftButton and self.dragStartPoint:
            x,y = e.x() , e.y()
            ox, oy = self.dragStartPoint
            dx2 = (x - ox) ** 2
            dy2 = (y - oy) ** 2
            d2 = dx2+dy2
            if d2 > MIN_DRAG_DISTANCE ** 2:
                mimeData = QtCore.QMimeData()
                mimeData.setText(self._key)
    
                drag = QtGui.QDrag(self)
                drag.setPixmap(self.icon().pixmap(32,32))
                drag.setMimeData(mimeData)
                #drag.setHotSpot(e.pos() - self.rect().topLeft())
    
                dropAction = drag.start(QtCore.Qt.MoveAction)
                self.setDown(False)
    def mousePressEvent(self, e):
        QtGui.QToolButton.mousePressEvent(self, e)
        if e.buttons() == QtCore.Qt.LeftButton:
            self.dragStartPoint = (e.x(), e.y())
            
        
    
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
        
        
        
    
