# encoding: UTF-8
import os.path, traceback
import logging, imp

from PyQt4 import QtGui, QtCore, uic

def load_module(name, path):
    fp = None
    module = None
    try:
        fp, pathname, description = imp.find_module(name,[path])

        module = imp.load_module(name, fp, pathname, description)
    except Exception:
        logging.exception("FATAL: Error trying to load module %s" % (repr(name)))
    if fp:
        fp.close()   
    return module
            
                  
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
            
        if "script" in self.actionobj.master:
            source_filepath = self.actionobj.filedir(self.actionobj.master["script"])
            pathname , sourcename = os.path.split(source_filepath)
            print pathname
            print sourcename
            try:
                self.sourcemodule = load_module(sourcename, pathname)
                self.masterscript = self.sourcemodule.MasterScript(self)
            except Exception, e:
                print repr(e)
                print traceback.format_exc()
                
