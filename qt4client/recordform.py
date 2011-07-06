# encoding: UTF-8
import os, os.path, traceback
import logging, imp
from projectloader import LlampexTable

from PyQt4 import QtGui, QtCore, uic

try:
    from llampexwidgets import LlItemView
except ImportError:
    LlItemView = None
    print "WARN: *** LlampexWidgets module not installed ***. Record Forms may be not renderable."
    

def h(*args): return os.path.realpath(os.path.join(os.path.dirname(os.path.abspath( __file__ )), *args))

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
            
                  
class LlampexRecordForm(QtGui.QWidget):
    def __init__(self, actionobj, prjconn, tmd, model, row):
        QtGui.QWidget.__init__(self)        
        self.actionobj = actionobj
        self.prjconn = prjconn
        self.model = model
        self.row = row
        self.tmd = tmd
        try:
            ui_filepath = self.actionobj.filedir(self.actionobj.record["form"])
            self.ui = uic.loadUi(ui_filepath,self)
        except Exception:
            self.layout = QtGui.QVBoxLayout()
            self.layout.addStretch()
            
            label = QtGui.QLabel("FATAL: An error ocurred trying to load the record form:")
            self.layout.addWidget(label)
            text = QtGui.QTextBrowser()
            text.setText(traceback.format_exc())
            self.layout.addWidget(text)

            self.layout.addStretch()
            self.setLayout(self.layout)
            return
        
        try:
            if "script" in self.actionobj.record:
                source_filepath = self.actionobj.filedir(self.actionobj.record["script"])
                pathname , sourcename = os.path.split(source_filepath)
                self.sourcemodule = load_module(sourcename, pathname)
                self.recordscript = self.sourcemodule.RecordScript(self)
        except Exception:
            msgBox = QtGui.QMessageBox()
            msgBox.setText("FATAL: An error ocurred trying to load the record script:\n" + traceback.format_exc())
            msgBox.setIcon(QtGui.QMessageBox.Critical)
            msgBox.exec_()            
        
                  

class LlampexQDialog( QtGui.QDialog ):
    def __init__( self, parent = None, widget = None, title = "Dialog Title"):
        QtGui.QDialog.__init__(self)
        self.widget = widget
        
        self.setWindowTitle(title)
        self.resize(300,105)
        self.setParent(parent)        
        self.setWindowFlags(QtCore.Qt.Sheet)
        
        self.setupUi()
  
        #self.buttonbox.accepted.connect( self.accept )
        #self.buttonbox.rejected.connect( self.reject )  
    
    def setupUi( self ):        
        self.vboxlayout = QtGui.QVBoxLayout(self)
        self.vboxlayout.setMargin(9)
        self.vboxlayout.setSpacing(6)
        self.vboxlayout.setObjectName("vboxlayout")
  
        self.hboxlayout = QtGui.QHBoxLayout()
        self.hboxlayout.setMargin(0)
        self.hboxlayout.setSpacing(6)
        self.hboxlayout.setObjectName("hboxlayout")

        self.buttonlayout = QtGui.QHBoxLayout()
        self.buttonlayout.setMargin(3)
        self.buttonlayout.setSpacing(0)
        self.buttonlayout.addStretch()
        """
        self.buttonbox = QtGui.QDialogButtonBox( QtGui.QDialogButtonBox.Yes | QtGui.QDialogButtonBox.No )
        self.buttonlayout.addWidget(self.buttonbox)
        """
        self.buttonprev = QtGui.QToolButton()
        self.buttonprev.setIcon(QtGui.QIcon(QtGui.QPixmap(h("./icons/previous.png"))))
        #self.buttonprev.setText("<")
        self.buttonnext = QtGui.QToolButton()
        self.buttonnext.setIcon(QtGui.QIcon(QtGui.QPixmap(h("./icons/next.png"))))
        #self.buttonnext.setText(">")
        self.buttonaccept = QtGui.QToolButton()
        self.buttonaccept.setIcon(QtGui.QIcon(QtGui.QPixmap(h("./icons/accept.png"))))
        #self.buttonaccept.setText(";)")
        self.buttonacceptcontinue = QtGui.QToolButton()
        self.buttonacceptcontinue.setIcon(QtGui.QIcon(QtGui.QPixmap(h("./icons/accepttocontinue.png"))))
        #self.buttonacceptcontinue.setText(":D")
        self.buttoncancel = QtGui.QToolButton()
        self.buttoncancel.setIcon(QtGui.QIcon(QtGui.QPixmap(h("./icons/cancel.png"))))
        #self.buttoncancel.setText("X")
        self.buttonlayout.addWidget(self.buttonprev)
        self.buttonlayout.addWidget(self.buttonnext)
        self.buttonlayout.addWidget(self.buttonaccept)
        self.buttonlayout.addWidget(self.buttonacceptcontinue)
        self.buttonlayout.addWidget(self.buttoncancel)
        
        self.vboxlayout.addWidget(self.widget)
        self.vboxlayout.addLayout(self.buttonlayout)
        self.setLayout(self.vboxlayout)    
        
        self.connect(self.buttonaccept, QtCore.SIGNAL("clicked()"), self, QtCore.SLOT("accept()"))
        self.connect(self.buttoncancel, QtCore.SIGNAL("clicked()"), self, QtCore.SLOT("reject()"))
    
    
class loadActionFormRecord():
    def __init__(self, parent = 0, windowAction = 'INSERT', actionobj = None, prjconn = None, tmd = None, model = None, rowItemIdx = None):
        self.parent = parent
        self.windowAction = windowAction
        self.actionobj = actionobj
        self.rpc = prjconn 
        self.tmd = tmd
        self.model = model
        self.row = rowItemIdx
        if self.model is None: 
            msgBox = QtGui.QMessageBox()
            msgBox.setText("FATAL: An error ocurred trying to load the table model:\n" + traceback.format_exc())
            msgBox.setIcon(QtGui.QMessageBox.Critical)
            msgBox.exec_()
            return 
            
        if self.row is None and self.windowAction != 'INSERT':
            msgBox = QtGui.QMessageBox()
            msgBox.setText("FATAL: No record data selected:\n" + traceback.format_exc())
            msgBox.setIcon(QtGui.QMessageBox.Critical)
            msgBox.exec_()
            return 
        
        if self.tmd is None: self.tmd = LlampexTable.tableindex[self.form.actionobj.table]
        
        print "Ui record file : ", self.actionobj.record["form"]
        self.recordUi = LlampexRecordForm(self.actionobj, self.rpc, self.tmd, self.model, self.row)
        self.showFormRecord()
        
    def showFormRecord(self):
        dialog = LlampexQDialog(self.parent, self.recordUi, "Articulos Form Record")        
        ret = dialog.exec_();
        print "RecordForm: ", ret
        
        
        
        
        
        
        