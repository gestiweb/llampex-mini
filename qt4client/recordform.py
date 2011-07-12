# encoding: UTF-8
import os, os.path, traceback
import logging, imp
from PyQt4 import QtGui, QtCore, uic

import threading
from projectloader import LlampexTable
from llitemview import LlItemView1

try:
    from llampexwidgets import LlItemView
except ImportError:
    LlItemView = None
    print "WARN: *** LlampexWidgets module not installed ***. Record Forms may be not renderable."


def h(*args): return os.path.realpath(os.path.join(os.path.dirname(os.path.abspath( __file__ )), *args))

def _getAllWidgets(form):
    widgets = []
    for obj in form.children():
        if isinstance(obj, QtGui.QWidget):
            widgets.append(obj)
            widgets+=_getAllWidgets(obj)
    return widgets

def getAllWidgets(form):
    return [ obj for obj in _getAllWidgets(form) if obj.objectName() ]

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
        self.setChildValuesFormRecord(self.ui)
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
            
    def setChildValuesFormRecord(self, form):
        for obj in getAllWidgets(form):
            if isinstance(obj, LlItemView):
                try:
                    column = self.tmd.fieldlist.index(obj.fieldName)
                except ValueError:
                    print "ERROR: FieldName %s does not exist" % (obj.fieldName)
                else:
                    widget = LlItemView1(obj)
                    widget.setObjectName(obj.objectName()+"_editor")
                    widget.setup()
                    widget.setModel(self.model)
                    widget.setPosition(self.row, column)
                    widget.setTabWidget(obj)
                    widget.setSizePolicy(QtGui.QSizePolicy.MinimumExpanding,QtGui.QSizePolicy.MinimumExpanding)
                    obj.replaceEditorWidget(widget)
        
    
    def delete(self): 
        #self.ui.hide()
        ret = self.ui.close()
        self.ui.deleteLater()
        self.actionobj = None
        self.prjconn = None
        self.model = None
        self.row = None
        self.tmd = None
        self.ui = None
        if hasattr(self.recordscript, "delete"):
            self.recordscript.delete()
        del self.recordscript
        self.close()
        self.deleteLater()
        return ret
        
        
                  
def lock(fn):
    def myfn(self,*args):
        if not self.lock.acquire(False):
            print "Blocking"
            self.lock.acquire()
        try:
            return fn(self,*args)
        finally:
            self.lock.release()
    return myfn
        

class LlampexQDialog( QtGui.QDialog ):
    def __init__( self, parent = None, widgetFactory = None, title = "Dialog Title"):
        QtGui.QDialog.__init__(self)
        self.lock = threading.Lock()
        self.widgetFactory = widgetFactory
        self.rowcount = 0
        self.widget = None
        self.setWindowTitle(title)
        self.resize(300,105)
        self.setParent(parent)        
        self.setWindowFlags(QtCore.Qt.Sheet)
        self.setupUi()
  
    @lock
    def createNewWidget(self, preserveRow = True):
        row = None
        if self.widget:
            if preserveRow: row = self.widget.row
            self.widgetlayout.removeWidget(self.widget)
            self.widget.delete()
            self.widget = None
        self.widget = self.widgetFactory(row = row)
        self.widgetlayout.addWidget(self.widget)
        self.rowcount = self.widget.model.rowCount()
        
    
    def createBottomButton(self, text = None, icon = None, action = None, key = None):
        wbutton = QtGui.QToolButton()
        if text:
            wbutton.setText(text)
        if icon:
            wbutton.setIcon(QtGui.QIcon(QtGui.QPixmap(h("./icons/%s.png" % icon))))
        wbutton.setMinimumSize(38, 38)
        wbutton.setMaximumSize(38, 38)
        wbutton.setIconSize(QtCore.QSize(22, 22))
        wbutton.setFocusPolicy(QtCore.Qt.NoFocus)
        if key:
            seq = QtGui.QKeySequence(key)
            wbutton.setShortcut(seq)
        self.buttonlayout.addWidget(wbutton)
        if action:
            if type(action) is tuple:
                self.connect(wbutton, QtCore.SIGNAL("clicked()"), *action)
            else:
                self.connect(wbutton, QtCore.SIGNAL("clicked()"), action)

        return wbutton

        
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
        self.statuslabel = QtGui.QLabel()
        self.buttonlayout.addWidget(self.statuslabel)
        self.buttonlayout.addStretch()
        """
        self.buttonbox = QtGui.QDialogButtonBox( QtGui.QDialogButtonBox.Yes | QtGui.QDialogButtonBox.No )
        self.buttonlayout.addWidget(self.buttonbox)
        """
        
        self.buttonfirst = self.createBottomButton(icon="first", action=self.first, key="F5")
        self.buttonprev = self.createBottomButton(icon="previous", action=self.prev, key="F6")
        self.buttonnext = self.createBottomButton(icon="next", action=self.next, key="F7")
        self.buttonlast = self.createBottomButton(icon="last", action=self.last, key="F8")
        self.buttonaccept = self.createBottomButton(icon="accept", action=(self,QtCore.SLOT("accept()")), key="F9")
        self.buttonacceptcontinue = self.createBottomButton(icon="accepttocontinue", action=self.acceptToContinue, key="F10")
        self.buttoncancel = self.createBottomButton(icon="cancel", action=(self,QtCore.SLOT("reject()")), key="ESC")
        
        self.widgetlayout = QtGui.QVBoxLayout()
        self.createNewWidget()
        
        self.vboxlayout.addLayout(self.widgetlayout)
        self.vboxlayout.addLayout(self.buttonlayout)
        self.setLayout(self.vboxlayout)    
        
        self.updateEnableStatus()
        self.updateStatusLabel()

    def getRowCount(self):
        return self.rowcount
        
    def updateEnableStatus(self):
        nonextrows = bool(self.widget.row >= (self.rowcount-1))
        noprevrows = bool(self.widget.row == 0)
        self.buttonfirst.setDisabled(noprevrows)
        self.buttonprev.setDisabled(noprevrows)
        self.buttonnext.setDisabled(nonextrows)
        self.buttonlast.setDisabled(nonextrows)
    
    def updateStatusLabel(self):
        row = self.widget.row
        self.statuslabel.setText("row number: %d/%d" % (row + 1, self.rowcount))

    def enforceRowLimits(self):
        if self.widget.row < 0: 
            self.widget.row = 0
        if self.widget.row > self.rowcount-1: 
            self.widget.row = self.rowcount-1
        
    def moveCursor(self, fn):
        self.widget.row = fn(self.widget.row)
        self.enforceRowLimits()
        self.createNewWidget()    
        self.updateEnableStatus()
        self.updateStatusLabel()
    
    def next(self):  self.moveCursor(lambda row: row+1)
    def prev(self):  self.moveCursor(lambda row: row-1)
    def first(self): self.moveCursor(lambda row: 0)
    def last(self):  self.moveCursor(lambda row: self.getRowCount() )
    
    
        
    def acceptToContinue( self ):
        print "AcceptToContinue Button Clicked"    
    
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
        # self.recordUi = self.recordFormFactory()
        self.showFormRecord()
    
    def recordFormFactory(self, row = None):
        if row is None: row = self.row
        return LlampexRecordForm(self.actionobj, self.rpc, self.tmd, self.model, row)
        
    def showFormRecord(self):
        dialog = LlampexQDialog(self.parent, self.recordFormFactory, "Articulos Form Record")        
        ret = dialog.exec_();
        print "RecordForm: ", ret
        
        
        
        
        
        
        