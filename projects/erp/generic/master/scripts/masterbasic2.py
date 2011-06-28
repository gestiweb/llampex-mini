# encoding: UTF-8
import os.path, traceback
from PyQt4 import QtGui, QtCore, uic
from PyQt4 import QtSql
from masterform import LlampexMasterForm
import time
import re
import qsqlrpcdriver.qtdriver as qtdriver
import threading

from projectloader import LlampexTable

def h(*args): return os.path.realpath(os.path.join(os.path.dirname(os.path.abspath( __file__ )), *args))
    

class MasterScript(object):
    def __init__(self, form):
        self.form = form
        self.rpc = self.form.prjconn
        
        # This code is obsolete! >>>>
        if not hasattr(self.rpc,"qtdriver"):
            print "####### LOADING QT-SQL DRIVER IN PROJECT CODE !!! #####"
            qtdriver.DEBUG_MODE = True
            self.rpc.qtdriver = qtdriver.QSqlLlampexDriver(self.rpc)
            self.rpc.qtdb = QtSql.QSqlDatabase.addDatabase(self.rpc.qtdriver, "llampex-qsqlrpcdriver")
            assert(self.rpc.qtdb.open("",""))
            qtdriver.DEBUG_MODE = False
        # <<< This code is obsolete!
        
        self.db = self.rpc.qtdb
        self.table = self.form.actionobj.table
        self.model = None
        print
        try:
            tmd=LlampexTable.tableindex[self.table]
            
            print tmd
            print "PKey:", tmd.primarykey
            print tmd.fieldlist
            print tmd.fields
            print "Nombre:", tmd.field.nombre
        except Exception, e:
            print "Error loading table metadata:", e
        print
        
        table = self.form.ui.table
        
        table.setSortingEnabled( True )
        
        tableheader = table.horizontalHeader()
        tableheader.setSortIndicator(0,0)
        tableheader.setContextMenuPolicy( QtCore.Qt.ActionsContextMenu )
        action_addfilter = QtGui.QAction(
                    QtGui.QIcon(h("../../icons/page-zoom.png")),
                    "Add &Filter...", tableheader)
        action_showcolumns = QtGui.QAction(
                    QtGui.QIcon(h("../../icons/preferences-actions.png")), 
                    "Show/Hide &Columns...", tableheader)
        action_hidecolumn = QtGui.QAction("&Hide this Column", tableheader)
        action_addfilter.setIconVisibleInMenu(True)
        action_showcolumns.setIconVisibleInMenu(True)
        tableheader.addAction(action_addfilter)
        tableheader.addAction(action_showcolumns)
        tableheader.addAction(action_hidecolumn)
        tableheader.setStretchLastSection(True)
         
        self.form.connect(action_addfilter, QtCore.SIGNAL("triggered(bool)"), self.action_addfilter_triggered)
        
        self.form.connect(tableheader, QtCore.SIGNAL("sortIndicatorChanged(int,Qt::SortOrder)"), self.table_sortIndicatorChanged)
        self.form.connect(tableheader, QtCore.SIGNAL("customContextMenuRequested(QPoint &)"),self.table_headerCustomContextMenuRequested)
        self.form.connect(self.form.ui.btnNew, QtCore.SIGNAL("clicked()"), self.btnNew_clicked)
        self.model = QtSql.QSqlTableModel(None,self.db)
        self.modelReady = threading.Event()
        self.modelSet = threading.Event()
        QtCore.QTimer.singleShot(5,self.settablemodel)
        thread1 = threading.Thread(target=self.reload_data)
        thread1.start()
        
    def btnNew_clicked(self):
        print "Button New clicked"
        dialog = QtGui.QDialog(self.form)
        dialog.setWindowTitle("Insert new record")
        ret = dialog.exec_()
        print ret
    
    def action_addfilter_triggered(self, checked):
        print "Add Filter triggered:", checked
        rettext, ok = QtGui.QInputDialog.getText(self.form, "Add New Filter",
            "Write New WHERE expression:", QtGui.QLineEdit.Normal, self.model.filter())
        self.model.setFilter(rettext)
        thread1 = threading.Thread(target=self.select_data)
        thread1.start()
    
    def table_headerCustomContextMenuRequested(self, point):
        print point
        
    def table_sortIndicatorChanged(self, column, order):
        print column, order
        
    def reload_data(self):
        #table = self.form.ui.table
        print "Model table:", self.table
        self.model.setTable(self.table)
        self.model.setSort(0,0)
        print "ok"
        self.model.setEditStrategy(QtSql.QSqlTableModel.OnRowChange)
        self.modelReady.set()
        self.modelSet.wait()
        # QtCore.QTimer.singleShot(100,self.settablemodel)
        self.select_data()
        
    def select_data(self):
        print "Selecting!"
        self.model.select()
        print "ok"
    
    def settablemodel(self):
        self.modelReady.wait()
        print ">Setting Table Model!"
        self.form.ui.table.setModel(self.model)
        print ">ok"
        self.modelSet.set()
            
        
