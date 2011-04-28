# encoding: UTF-8
print "loading customers.py"
import os.path, traceback
from PyQt4 import QtGui, QtCore, uic
from masterform import LlampexMasterForm
import time
import re
import threading

class DataLoaderThread(threading.Thread):
    maxrowscached = 100000
    def run(self):
        p = self.parent
        self.abort = False
        self.totalrowcount = 0
        while True:
            rowcount = 0
            results = []
            for i in range(2):
                results.append( p.cursor.method.fetch(p.rowsperfecth) )
            
            while True:
                if self.abort: return
                newresult = p.cursor.method.fetch(p.rowsperfecth)
                rows = results.pop(0).value
                rowcount += len(rows)
                results.append(newresult)
                if not rows:
                    break
                p.cachedata += rows
            self.totalrowcount += rowcount
            if rowcount == 0 or self.totalrowcount > self.maxrowscached: 
                if self.totalrowcount > self.maxrowscached:
                    print "WARN: Stopped caching data because loader has reached %d rows" % (self.totalrowcount)
                p.execute(1)
                break
            if self.abort: return
            p.execute(5000)

class MasterScript(object):
    def __init__(self, form):
        self.form = form
        self.rpc = self.form.prjconn
        self.cursor = self.rpc.call.newCursor()
        self.table = self.form.actionobj.table
        self.timer = QtCore.QTimer(self.form)

        table = self.form.ui.table
        table.setRowCount(0)
        table.setColumnCount(1)
        table.setHorizontalHeaderLabels(["wait, loading data . . . "])
        
        self.form.connect(self.timer, QtCore.SIGNAL("timeout()"), self.timer_timeout)
        self.form.connect(table, QtCore.SIGNAL("cellDoubleClicked(int,int)"), self.table_cellDoubleClicked)
        tableheader = table.horizontalHeader()
        self.form.connect(tableheader, QtCore.SIGNAL("sectionClicked(int)"), self.table_sectionClicked)
        
        self.filterdata = {}
        self.filter_regex = r"(\w+)[ ]*(~|=|>|<|LIKE|ILIKE|>=|<=)[ ]*'(.+)'"
        
        self.sqlquery = None
        self.datathread = None
        self.cachedata = []
        self.data_reload()
        self.maxtablerows = 5000
        self.firstfetch = 50
    
    def table_cellDoubleClicked(self, row, col):
        print "Clicked", row,col
        
    def table_sectionClicked(self, col):
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
        if self.datathread:
            if self.datathread.isAlive():
                self.datathread.abort = True
                self.datathread.join(0.5)
                if self.datathread.isAlive():
                    print "WARN: DataThreadLoader still alive."
                del self.datathread
                self.datathread = None
                
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
            if not self.timer_initload():
                return
        self.timer_populatetable()
        
    def execute(self,rows):
        offset = len(self.cachedata)
        limit = rows
        try:
            self.cursor.call.execute(self.sqlquery + " LIMIT %d OFFSET %d" % (limit,offset))
        except Exception, e:
            print "FATAL: Cursor Execute failed with:", repr(e)
            self.cursor.call.rollback()
            self.timer.stop()
            return False
        self.totalrows += self.cursor.call.rowcount()
        # print "%s: %d rows" % (self.table,self.totalrows)
        return True
        
    def timer_initload(self):
        table = self.form.ui.table
        self.cachedata[:] = []
        if not self.execute(self.firstfetch):
            table.setRowCount(0)
            return False
        field_list = self.cursor.call.fields()[:self.maxcolumns]
        table.setColumnCount(len(field_list))
        table.setHorizontalHeaderLabels(field_list)
        
        tableheader = self.form.ui.table.horizontalHeader()
        # tableheader.setClickable(False)  # default is True
        tableheader.setSortIndicatorShown(True)
        tableheader.setMovable(True)
        tableheader.setStretchLastSection(True)
        
        table.setRowCount(min([self.totalrows,self.maxtablerows]))
        
        self.lastreporttime = time.time()
        self.nrows = 0
        self.nrow = 0      
        self.omitted = 0  
        self.rowsperfecth = 10

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

        
        
        