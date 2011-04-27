# encoding: UTF-8
print "loading customers.py"
import os.path, traceback
from PyQt4 import QtGui, QtCore, uic
from masterform import LlampexMasterForm
import time
import re
import threading

class DataLoaderThread(threading.Thread):
    def run(self):
        p = self.parent
        while True:
            rowcount = 0
            results = []
            for i in range(3):
                results.append( p.cursor.method.fetch(p.rowsperfecth) )
            
            while True:
                newresult = p.cursor.method.fetch(p.rowsperfecth)
                rows = results.pop(0).value
                rowcount += len(rows)
                results.append(newresult)
                if not rows:
                    break
                p.cachedata += rows
            if rowcount == 0: 
                p.execute(1)
                break
            p.execute(5000)

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
        
        self.sqlquery = None
        self.datathread = None
        self.cachedata = []
        self.data_reload()
        self.maxtablerows = 500
    
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
            fullreload = False
            self.update_sqlquery()
            if self.datathread is None: fullreload = True
            else:
                if self.sqlquery != self.datathread.sql: fullreload = True
                
            if fullreload:
                self.data_reload()
            else:
                self.data_softreload()
    
    def update_sqlquery(self):
        where_str = []
        for col, regex in self.filterdata.iteritems():
            result1 = re.match(self.filter_regex,regex)
            if result1:
                fieldname, operator, regexvalue = result1.group(1), result1.group(2), result1.group(3)
                print "adding:", fieldname, operator, regexvalue
                where_str.append("%s %s '%s'" % (fieldname, operator ,regexvalue))
        
        self.sqlquery = "SELECT * FROM \"%s\"" % self.table
        if where_str:
            self.sqlquery += " WHERE %s" % (" AND ".join(where_str))
    
    def data_reload(self):
        table = self.form.ui.table
        table.setRowCount(0)
        table.setColumnCount(1)
        table.setHorizontalHeaderLabels(["wait, loading data . . . "])
        self.maxcolumns = 32
        self.starttime = time.time()
        print "started full reload for", self.table
        self.totalrows = 0
        self.update_sqlquery()
        
        self.datathread = DataLoaderThread()
        self.datathread.parent = self
        self.datathread.daemon = True
        self.datathread.sql = self.sqlquery
        self.table_initialized = False
        self.timer.start(10)

    def data_softreload(self):
        table = self.form.ui.table
        self.starttime = time.time()
        print "started soft reload for", self.table
        self.nrows = 0
        self.nrow = 0        
        self.omitted = 0  
        self.totalrows = len(self.cachedata)
        table.setRowCount(min([self.totalrows,self.maxtablerows]))
        self.timer.start(150)
    
        
    def timer_timeout(self):
        if self.table_initialized == False:
            self.timer_initload()
        self.timer_populatetable()
        
    def execute(self,rows):
        offset = len(self.cachedata)
        limit = rows
        try:
            self.cursor.call.execute(self.sqlquery + " LIMIT %d OFFSET %d" % (limit,offset))
        except Exception, e:
            print repr(e)
            self.cursor.call.rollback()
            self.timer.stop()
            return
        self.totalrows += self.cursor.call.rowcount()
        print "%s: %d rows" % (self.table,self.totalrows)
        
    def timer_initload(self):
        table = self.form.ui.table
        self.cachedata[:] = []
        self.execute(self.maxtablerows)
        field_list = self.cursor.call.fields()[:self.maxcolumns]
        table.setColumnCount(len(field_list))
        table.setHorizontalHeaderLabels(field_list)
        
        table.setRowCount(min([self.totalrows,self.maxtablerows]))
        
        self.lastreporttime = time.time()
        self.nrows = 0
        self.nrow = 0      
        self.omitted = 0  
        self.rowsperfecth = 50

        self.datathread.start()
        
        #self.fetchresult = self.cursor.method.fetch(self.rowsperfecth)
        self.table_initialized = True
        self.timer.start(150)

    
    
    
    def timer_populatetable(self):
        #self.fetchresult.conn.dispatch_until_empty()
        #if self.fetchresult.response is None: return
        #rowlist = self.fetchresult.value
        #self.fetchresult = self.cursor.method.fetch(self.rowsperfecth)
        
        rowlist = self.cachedata[self.nrows:]
        table = self.form.ui.table
        if not rowlist and not self.datathread.isAlive():
            
            print "finished loading data for %s (%d rows) in %.3f seconds" % (
                self.table, self.totalrows, time.time() - self.starttime)
            #x = self.fetchresult.value #get and drop.
            #assert( not x ) # should be empty
            self.timer.stop() 
            
        if not rowlist:
            return 
            
        self.nrows += len(rowlist)
        self.table_loaddata(rowlist)
    
    def table_loaddata(self, rowlist):
        table = self.form.ui.table
        omittedrows = 0
        table.setRowCount(self.nrow+len(rowlist))
        for rowdata in rowlist:
            includerow = True
            if self.nrow > self.maxtablerows: includerow = False
            for col, regex in self.filterdata.iteritems():
                if col < 0 or col >= len(rowdata): continue
                result1 = re.match(self.filter_regex,regex)
                if result1: continue
                val = unicode(rowdata[col])
                if not re.search(regex,val, re.I): 
                #if not val.startswith(regex):
                    includerow = False
                    break
                    
            if not includerow: 
                omittedrows += 1
                self.omitted += 1  
                continue
            for ncol, value in enumerate(rowdata[:self.maxcolumns]):
                item = QtGui.QTableWidgetItem(unicode(value))
                table.setItem(self.nrow, ncol, item)
            self.nrow += 1
        if self.nrow == 0:
            table.setRowCount(1)
        else:
            table.setRowCount(self.nrow)
        #table.setRowCount(min([self.totalrows,self.maxtablerows]))

        if time.time() - self.lastreporttime > 1:
            self.lastreporttime = time.time()
            print "loading table %s: %d rows (+%d hidden) (%.2f%%)" % (self.table, 
                self.nrow, self.omitted, float(self.nrow+self.omitted)*100.0/float(self.totalrows))

        
        
        