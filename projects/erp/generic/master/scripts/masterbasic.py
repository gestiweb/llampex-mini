# encoding: UTF-8
print "loading customers.py"
import os.path, traceback
from PyQt4 import QtGui, QtCore, uic
from masterform import LlampexMasterForm


class MasterScript(object):
    def __init__(self, form):
        self.form = form
        self.rpc = self.form.prjconn
        self.cursor = self.rpc.call.newCursor()
        self.table = self.form.actionobj.table
        
        print "started init"
        self.cursor.call.execute("SELECT * FROM \"%s\"" % self.table)
        table = self.form.ui.table
        field_list = self.cursor.call.fields()
        table.setColumnCount(len(field_list))
        table.setHorizontalHeaderLabels(field_list)
        nrows = 0
        nrow = 0
        table.setRowCount(nrows)
        while True:
            rowlist = self.cursor.call.fetch()
            print ":", repr(rowlist)
            if not rowlist: break
            nrows += len(rowlist)
            table.setRowCount(nrows)
            for rowdata in rowlist:
                for ncol, value in enumerate(rowdata):
                    item = QtGui.QTableWidgetItem(unicode(value))
                    table.setItem(nrow, ncol, item)
                nrow += 1
                    
             
        
        
        