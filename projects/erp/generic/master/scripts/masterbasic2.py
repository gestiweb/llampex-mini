# encoding: UTF-8
print "loading customers.py"
import os.path, traceback
from PyQt4 import QtGui, QtCore, uic
from PyQt4 import QtSql
from masterform import LlampexMasterForm
import time
import re
import qsqlrpcdriver.qtdriver as qtdriver
import threading

class MasterScript(object):
    def __init__(self, form):
        self.form = form
        self.rpc = self.form.prjconn
        if not hasattr(self.rpc,"qtdriver"):
            qtdriver.DEBUG_MODE = True
            self.rpc.qtdriver = qtdriver.QSqlLlampexDriver(self.rpc)
            self.rpc.qtdb = QtSql.QSqlDatabase.addDatabase(self.rpc.qtdriver, "llampex-qsqlrpcdriver")
            assert(self.rpc.qtdb.open("",""))
            qtdriver.DEBUG_MODE = False
        self.db = self.rpc.qtdb
        self.table = self.form.actionobj.table
        self.model = None

        
        table = self.form.ui.table
        #tableheader = table.horizontalHeader()
        self.form.ui.update()
        
        self.model = QtSql.QSqlTableModel(None,self.db)
        self.modelReady = threading.Event()
        self.modelSet = threading.Event()
        QtCore.QTimer.singleShot(5,self.settablemodel)
        thread1 = threading.Thread(target=self.reload_data)
        thread1.start()
        
        
    def reload_data(self):
        #table = self.form.ui.table
        print "Model table:", self.table
        self.model.setTable(self.table)
        print "ok"
        self.model.setEditStrategy(QtSql.QSqlTableModel.OnManualSubmit)
        self.modelReady.set()
        self.modelSet.wait()
        # QtCore.QTimer.singleShot(100,self.settablemodel)
        print "Selecting!"
        self.model.select()
        print "ok"
    
    def settablemodel(self):
        self.modelReady.wait()
        print ">Setting Table Model!"
        self.form.ui.table.setModel(self.model)
        print ">ok"
        self.modelSet.set()
            
        
