# encoding: UTF-8
import os.path, traceback

from PyQt4 import QtGui, QtCore, uic
      
class LlampexMasterForm(QtGui.QWidget):        
    def __init__(self, windowkey, actionobj):
        QtGui.QWidget.__init__(self)
        self.windowkey = windowkey
        self.actionobj = actionobj
        try:
            ui_filepath = self.actionobj.filedir(self.actionobj.master["form"])
            self.ui = uic.loadUi(ui_filepath,self)
        except Exception:
            self.layout = QtGui.QVBoxLayout()
            self.layout.addStretch()
            
            label = QtGui.QLabel("FATAL: An error ocurred trying to load the master form:")
            self.layout.addWidget(label)
            text = QtGui.QTextBrowser()
            text.setText(traceback.format_exc())
            self.layout.addWidget(text)

            self.layout.addStretch()
            self.setLayout(self.layout)
            
        