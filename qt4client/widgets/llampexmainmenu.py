#!/usr/bin/env python

from PyQt4 import QtCore, QtGui
import math, sys, random


class LlampexMainMenuItemList(QtGui.QFrame):
    def __init__(self, parent=None):
        super(LlampexMainMenuItemList, self).__init__(parent)
        self.llampex_layout = QtGui.QVBoxLayout()
        self.llampex_items = []
        self.setMinimumHeight(36)
        self.setMaximumHeight(5000)
        self.llampex_layout.setSizeConstraint(QtGui.QLayout.SetMinAndMaxSize)
        self.setLayout(self.llampex_layout)

    def llampex_addItem(self, textobj):
        if isinstance(textobj,basestring):
            llampex_item = QtGui.QCommandLinkButton(textobj)
        elif isinstance(textobj,QtGui.QCommandLinkButton):
            llampex_item = textobj
        else:
            raise ValueError, "The 1st argument isn't either a string nor a QtGui.QCommandLinkButton!"
        llampex_item.setMinimumHeight(36)
        llampex_item.setMaximumHeight(36)
        self.llampex_items.append(llampex_item)
        self.llampex_layout.insertWidget(self.llampex_layout.count()-1,llampex_item,1)
        return llampex_item
        
    addItem = llampex_addItem
    
    


class LlampexMainMenuItem(QtGui.QFrame):
    def __init__(self, text="Button", parent=None):
        super(LlampexMainMenuItem, self).__init__(parent)
        self.llampex_layout = QtGui.QVBoxLayout()
        
        self.llampex_cmdbutton = QtGui.QCommandLinkButton(text)
        self.llampex_subitems = LlampexMainMenuItemList() # Cambiar luego por un widget distinto.
        self.button = self.llampex_cmdbutton

        self.llampex_cmdbutton.setCheckable(True) # Checked es mostrado.
        self.llampex_cmdbutton.setMaximumHeight(36)
        self.llampex_cmdbutton.setMinimumHeight(36)
        self.llampex_cmdbutton.setMinimumWidth(200)
        
        self.llampex_subitems.setVisible(False)
        self.llampex_subitems.setMinimumHeight(30)
        
        self.llampex_layout.addWidget(self.llampex_cmdbutton)
        self.llampex_layout.addWidget(self.llampex_subitems)
        self.setMinimumHeight(20)
        self.setMaximumHeight(5000)

        self.llampex_layout.setSizeConstraint(QtGui.QLayout.SetMinAndMaxSize)

        self.setLayout(self.llampex_layout)

        self.connect( self.llampex_cmdbutton, QtCore.SIGNAL("toggled(bool)"),   self.llampex_subitems.setVisible )

    def llampex_addItem(self, text):
        return self.llampex_subitems.llampex_addItem(text)
    addItem = llampex_addItem
        

class LlampexMainMenuFrame(QtGui.QFrame):
    def __init__(self, parent=None):
        super(LlampexMainMenuFrame, self).__init__(parent)

        self.llampex_layout = QtGui.QVBoxLayout()
        self.llampex_items = []
        self.llampex_layout.addStretch()
        self.llampex_layout.setSizeConstraint(QtGui.QLayout.SetMinimumSize)
        self.setLayout(self.llampex_layout)
        #self.setFrameStyle(QtGui.QFrame.Panel | QtGui.QFrame.Raised);

    def llampex_addItem(self, textobj):
        if isinstance(textobj,basestring):
            llampex_item = LlampexMainMenuItem(textobj)
        elif isinstance(textobj,LlampexMainMenuItem):
            llampex_item = textobj
        else:
            raise ValueError, "The 1st argument isn't either a string nor a Item Object!"
        
        self.llampex_items.append(llampex_item)
        self.llampex_layout.insertWidget(self.llampex_layout.count()-1,llampex_item,1)
        return llampex_item
        

class LlampexMainMenu(QtGui.QScrollArea):
    def __init__(self, parent=None):
        super(LlampexMainMenu, self).__init__(parent)
        self.mywidget = LlampexMainMenuFrame()
        self.setWidget(self.mywidget)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        #self.setMinimumWidth(230)


class LlampexDockMainMenu(QtGui.QDockWidget):
    def __init__(self, parent=None):
        super(LlampexDockMainMenu, self).__init__(parent)
        
        self.mywidget = LlampexMainMenu() # Se carga en memoria
        self.setWidget(self.mywidget) # y se establece que es el control contenido por el Dock.
    
    def addItem(self, item):
        return self.mywidget.mywidget.llampex_addItem(item)

if __name__ == "__main__": # programa de demo.
    app = QtGui.QApplication(sys.argv)
    form1scroll = LlampexMainMenu()
    form1scroll.resize(350,500)
    form1 = form1scroll.mywidget
    boton = QtGui.QCommandLinkButton("pppp")
    for i in range(random.randint(3,7)):
        llampex_item = LlampexMainMenuItem("texto %d" % i)
        #llampex_item = form1.llampex_addItem("texto %d" % i)
        for j in range(random.randint(1,7)):
            llampex_item.llampex_addItem("subtexto %d.%d" % (i,j))
            #llampex_item.llampex_addItem(boton)
        form1.llampex_addItem(llampex_item)
            
    form1scroll.show()
    sys.exit(app.exec_())
