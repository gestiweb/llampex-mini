#!/usr/bin/env python
# encoding: UTF-8

from PyQt4 import QtCore, QtGui

class LlampexToolBarButton(QtGui.QToolButton):
    def __init__(self, key, actionobj, parent=None):
        super(QtGui.QToolButton, self).__init__(parent)
        self.parent = parent
        self.key = key
        self.actionobj = actionobj
        self.setup()
    
    def setup(self):
        icon = None
        if self.actionobj.icon:
            iconfile = self.actionobj.filedir(self.actionobj.icon)
            icon = QtGui.QIcon(iconfile)
                
        self.setToolTip(self.actionobj.name)
        self.setIcon(icon)
        self.setCursor(QtCore.Qt.PointingHandCursor)
        self.setStyleSheet("QToolButton { border: none; padding: 0px; }")
        
        self.connect(self, QtCore.SIGNAL("clicked()"), self.clicked)
        
    def clicked(self,checked=False):
        self.parent.parent.actionbutton_clicked(str(self.key))
    
    def mouseMoveEvent(self, e):
        mimeData = QtCore.QMimeData()
        mimeData.setText(self.key)
        
        drag = QtGui.QDrag(self)
        drag.setPixmap(self.icon().pixmap(16,16))
        drag.setMimeData(mimeData)
        drag.setHotSpot(e.pos() - self.rect().topLeft())
        
        self.parent.layout().removeWidget(self)
        self.parent.keys.remove(self.key)
        self.hide()
        
        dropAction = drag.start(QtCore.Qt.MoveAction)
        

class LlampexToolBar(QtGui.QFrame):
    
    def __init__(self, parent):
        QtGui.QFrame.__init__(self)
        self.parent = parent
        self.setup()
    
    def setup(self):
        self.setAcceptDrops(True)
        self.setFrameShape(QtGui.QFrame.StyledPanel)
        self.setFrameShadow(QtGui.QFrame.Raised)
        self.setLayout(QtGui.QHBoxLayout(self))
        self.layout().setContentsMargins(2,2,2,2)
        self.keys=[]
        
        self.line = QtGui.QFrame()
        self.line.setFrameShape(QtGui.QFrame.VLine);
        self.line.setFrameShadow(QtGui.QFrame.Sunken);
        self.line.hide()
    
    def dragEnterEvent(self, e):
        #print "in!"
        e.accept()
    
    def dragLeaveEvent(self, e):
        #print "out!"
        self.layout().removeWidget(self.line)
        self.line.hide()
        e.accept()

    def dropEvent(self, e):
        pos = e.pos()
        self.layout().removeWidget(self.line)
        self.line.hide()
        
        if (isinstance(e.source(), LlampexToolBarButton)):
            widget = e.source()
            del widget

        self.addToolButton(e.mimeData().text(),pos.x())
        e.setDropAction(QtCore.Qt.CopyAction)
        e.accept()
        
    def dragMoveEvent(self, e):
        pos = e.pos().x()
        
        self.layout().removeWidget(self.line)
        self.line.hide()
        
        #find position
        for i in range(self.layout().count()):
            widget = self.layout().itemAt(i).widget()
            if (widget.x() > pos):
                break
        
        self.layout().insertWidget(i,self.line)
        self.line.show()
        e.accept()
        
    def addToolButton(self,key,pos):
        print "Add "+key
        
        print self.keys
        if (str(key) not in self.keys):
            print "Gogogo!"
            index = str(key.split(".")[2])
            
            actionobj = self.parent.project.action_index[index]
            tb = LlampexToolBarButton(key,actionobj,self)
            
            #find position
            for i in range(self.layout().count()):
                widget = self.layout().itemAt(i).widget()
                if (widget.x() > pos):
                    break
            
            self.layout().insertWidget(i,tb)
            
            self.keys.append(str(key))

class LlampexSearchBox(QtGui.QLineEdit):
    
    def __init__(self, parent):
        QtGui.QLineEdit.__init__(self)
        
        self.clearButton = QtGui.QToolButton(self)
        pixmap = QtGui.QPixmap("icons/searchclear.png")
        self.clearButton.setIcon(QtGui.QIcon(pixmap))
        self.clearButton.setIconSize(pixmap.size())
        self.clearButton.setCursor(QtCore.Qt.ArrowCursor)
        self.clearButton.setStyleSheet("QToolButton { border: none; padding: 0px; }")
        self.clearButton.hide()
        self.connect(self.clearButton, QtCore.SIGNAL("clicked()"), self.clearClicked)
        self.connect(self,QtCore.SIGNAL("textChanged(const QString&)"), self.updateClearButton)
        self.frameWidth = self.style().pixelMetric(QtGui.QStyle.PM_DefaultFrameWidth)
        self.setStyleSheet(QtCore.QString("QLineEdit { padding-right: %1px; color: gray; } ").arg(self.clearButton.sizeHint().width()+self.frameWidth+1))
        self.setText("Search...")
        msz = self.minimumSizeHint()
        self.setMinimumSize(self.qMax(msz.width(), self.clearButton.sizeHint().height() + self.frameWidth * 2 + 2),
                            self.qMax(msz.height(), self.clearButton.sizeHint().height() + self.frameWidth * 2 + 2))
    
    def qMax(self, a1,  a2):
        if a1 <= a2:
            return a2
        else:
            return a1
    
    def clearClicked(self):
        self.clear()
    
    def resizeEvent(self, event):
        sz = self.clearButton.sizeHint()
        self.frameWidth = self.style().pixelMetric(QtGui.QStyle.PM_DefaultFrameWidth)
        self.clearButton.move(self.rect().right() - self.frameWidth - sz.width(), (self.rect().bottom() + 1 - sz.height())/2)
    
    def focusInEvent(self, event):
        QtGui.QLineEdit.focusInEvent(self, event)
        if (self.text() == "Search..."):
            self.setStyleSheet(QtCore.QString("QLineEdit { padding-right: %1px; color: black } ").arg(self.clearButton.sizeHint().width()+self.frameWidth+1))
            self.setText("")
            
    def focusOutEvent(self,event):
        QtGui.QLineEdit.focusOutEvent(self, event)
        if (self.text().isEmpty()):
            self.setStyleSheet(QtCore.QString("QLineEdit { padding-right: %1px; color: gray } ").arg(self.clearButton.sizeHint().width()+self.frameWidth+1))
            self.setText("Search...")
        
    def updateClearButton(self, text):
        if (text.isEmpty() or text == "Search..."):
            self.clearButton.setVisible(False) 
        else:
            self.clearButton.setVisible(True)