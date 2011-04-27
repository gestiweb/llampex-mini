#!/usr/bin/env python
# encoding: UTF-8

from PyQt4 import QtCore, QtGui
import sys, time, gc

class LlampexTable(QtGui.QTableView):
    def __init__(self):
        QtGui.QTableView.__init__(self)
        self.contextmenu = QtGui.QMenu("Properties")
        self.contextmenu.addAction("Configure server filters") 
        self.contextmenu.addAction("Configure server orderby") 
        self.contextmenu.addAction("Show/hide columns") 
        self.contextmenu.addAction("x") 
        self.connect(self.contextmenu, QtCore.SIGNAL("triggered(QAction*)"), self.contextmenu_triggered)
        self.model = QtGui.QStandardItemModel()
        self.setModel(self.model)
        self.model.setColumnCount(15)
        for i in range(250):
            self.model.appendRow( [ QtGui.QStandardItem("z%d:%d" % (x,i)) for x in range(5) ] )
        self.ncount = 5000
        
    def contextmenu_triggered(self, action):
        print "Activated action:", unicode(action.text())
        if unicode(action.text()) == "x":
            del self.model 
            self.close()
            return
        
        self.ncount *= 2
        t1 = time.time()
        rows = self.model.rowCount()
        startrow = rows
        rows += self.ncount
        self.model.setRowCount(rows)
        z = 0
        for i in range(self.ncount):
            for x in range(15):
                z+=1
                mytext = "x%d:%d:%d" % (i,x,z)
                item = QtGui.QStandardItem(mytext) 
                self.model.setItem( i+startrow , x  , item )
                
        print "Added %d rows in %.3fms. (%.2f cells / s)" % (self.ncount, (time.time() - t1)*1000.0, z / (time.time() - t1))
        
        
    def contextMenuEvent(self,event):
        print "Context menu:", event.pos()
        self.contextmenu.popup(event.globalPos())
        

class MyDialog(QtGui.QDialog):
    def __init__(self):
        QtGui.QDialog.__init__(self)
        self.setWindowTitle("Test Llampex Table")
        self.layout = QtGui.QVBoxLayout()
        
        self.table = LlampexTable()
        self.layout.addWidget(self.table)
        self.table.parent = self
        self.setLayout(self.layout)
        self.resize(500,300)
        self.timer = QtCore.QTimer()
        self.connect(self.timer, QtCore.SIGNAL("timeout()"), self.timer_timeout)
        self.timer.start(3000)
        
    def timer_timeout(self):
        print "collect!" , gc.collect()
        
        xl = gc.get_objects()
        cnt = {}
        problem = []
        for x in xl:
            tx = type(x)
            if tx not in cnt: cnt[tx] = 0 
            cnt[tx] += 1
            
        for tx in cnt:
            if cnt[tx] > 1000: 
                problem.append(tx)
                print tx, cnt[tx]
            
        
        print len(cnt), len(xl)
    



def main():
    gc.disable()
    app = QtGui.QApplication(sys.argv)
    dialog = MyDialog()
    dialog.show()
    retval = app.exec_() 
    sys.exit(retval) 

if __name__ == "__main__":
    main()
