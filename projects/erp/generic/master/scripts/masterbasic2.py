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
            #qtdriver.DEBUG_MODE = False
        self.db = self.rpc.qtdb
        self.table = self.form.actionobj.table
        self.model = None

        
        table = self.form.ui.table
        #tableheader = table.horizontalHeader()
        self.form.ui.update()
        
        self.model = QtSql.QSqlTableModel(None,self.db)
        self.modelReady = threading.Event()
        QtCore.QTimer.singleShot(100,self.settablemodel)
        thread1 = threading.Thread(target=self.reload_data)
        thread1.start()
        
        
    def reload_data(self):
        #table = self.form.ui.table
        self.model.setTable(self.table)
        self.model.setEditStrategy(QtSql.QSqlTableModel.OnManualSubmit)
        self.modelReady.set()
        # QtCore.QTimer.singleShot(100,self.settablemodel)
        self.model.select()
    
    def settablemodel(self):
        self.modelReady.wait()
        print "Setting Table Model!"
        self.form.ui.table.setModel(self.model)
            
        
