# encoding: UTF-8
print "loading customers.py"
import os.path, traceback
from PyQt4 import QtGui, QtCore, uic
from masterform import LlampexMasterForm
import time
import re
#import threading

#class DataLoaderThread(Thread):
#    def run():
#        p = self.parent
        

class MasterScript(object):
    def __init__(self, form):
        self.form = form
        self.rpc = self.form.prjconn
        self.cursor = self.rpc.call.newCursor()
        self.table = self.form.actionobj.table
        self.timer = QtCore.QTimer(self.form)
        self.form.connect(self.timer, QtCore.SIGNAL("timeout()"), self.timer_timeout)
        self.form.connect(self.form.ui.table, QtCore.SIGNAL("cellDoubleClicked(int,int)"), self.table_cellDoubleClicked)
        self.filterdata = {}
        self.filter_regex = r"(\w+)[ ]*(~|=|>|<|LIKE|ILIKE|>=|<=)[ ]*'(.+)'"
        #self.cachedata = []
        self.data_reload()
    
    def table_cellDoubleClicked(self, row, col):
        if col not in self.filterdata:
            line1 = "No filter declared yet for column %d" % col
            txt = ""
        else:
            line1 = "Replacing filter for column %d: %s" % (col, self.filterdata[col])
            txt = unicode(self.filterdata[col])
        rettext, ok = QtGui.QInputDialog.getText(self.form, "Filter By",
            line1 + "\nWrite New filter (RegEx):", QtGui.QLineEdit.Normal, txt)
        rettext = unicode(rettext)
        if ok:
            print "New filter:", repr(rettext)
            if rettext == u"":
                if col in self.filterdata:
                    del self.filterdata[col]
            else:
                self.filterdata[col] = rettext
            self.data_reload()
    
    
    def data_reload(self):
        table = self.form.ui.table
        table.setRowCount(0)
        table.setColumnCount(1)
        table.setHorizontalHeaderLabels(["wait, loading data . . . "])
        self.maxcolumns = 6
        self.starttime = time.time()
        print "started init for", self.table
        self.table_initialized = False
        self.timer.start(5)
        
    def timer_timeout(self):
        if self.table_initialized == False:
            self.timer_initload()
        else:
            self.timer_populatetable()
        
    def timer_initload(self):
        table = self.form.ui.table
        where_str = []
        for col, regex in self.filterdata.iteritems():
            result1 = re.match(self.filter_regex,regex)
            if result1:
                fieldname, operator, regexvalue = result1.group(1), result1.group(2), result1.group(3)
                print "adding:", fieldname, regexvalue
                where_str.append("%s %s '%s'" % (fieldname, operator ,regexvalue))
        
        if where_str:
            self.cursor.call.execute("SELECT * FROM \"%s\" WHERE %s" % (self.table," AND ".join(where_str)))
        else:    
            self.cursor.call.execute("SELECT * FROM \"%s\"" % self.table)
        self.totalrows = self.cursor.call.rowcount()
        print "%s: %d rows" % (self.table,self.totalrows)
        field_list = self.cursor.call.fields()[:self.maxcolumns]
        table.setColumnCount(len(field_list))
        table.setHorizontalHeaderLabels(field_list)
        self.lastreporttime = time.time()
        self.nrows = 0
        self.nrow = 0        
        self.rowsperfecth = 600
        self.fetchresult = self.cursor.method.fetch(self.rowsperfecth)
        table.setRowCount(self.totalrows)
        self.table_initialized = True
    
    
    def timer_populatetable(self):
        self.fetchresult.conn.dispatch_until_empty()
        if self.fetchresult.response is None: return
        rowlist = self.fetchresult.value
        self.fetchresult = self.cursor.method.fetch(self.rowsperfecth)
        table = self.form.ui.table
        if not rowlist:
            
            print "finished loading data for %s (%d rows) in %.3f seconds" % (
                self.table, self.totalrows, time.time() - self.starttime)
            x = self.fetchresult.value #get and drop.
            assert( not x ) # should be empty
            self.timer.stop() 
        self.nrows += len(rowlist)
        #table.setRowCount(self.nrows)
        omittedrows = 0
        for rowdata in rowlist:
            includerow = True
            for col, regex in self.filterdata.iteritems():
                if col < 0 or col >= len(rowdata): continue
                result1 = re.match(self.filter_regex,regex)
                if result1: continue
                val = unicode(rowdata[col])
                #if not re.search(regex,val, re.I): 
                if not val.startswith(regex):
                    includerow = False
                    break
                    
            if not includerow: 
                omittedrows += 1
                continue
            for ncol, value in enumerate(rowdata[:self.maxcolumns]):
                item = QtGui.QTableWidgetItem(unicode(value))
                table.setItem(self.nrow, ncol, item)
            self.nrow += 1
        self.totalrows -= omittedrows
        if self.totalrows < 1: self.totalrows = 1
        table.setRowCount(self.totalrows)

        if time.time() - self.lastreporttime > 1:
            self.lastreporttime = time.time()
            print "loading table %s: %d rows (%.2f%%)" % (self.table, 
                self.nrow, float(self.nrow)*100.0/float(self.totalrows))

        
        
        