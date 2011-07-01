# encoding: UTF-8
import os.path, traceback
from PyQt4 import QtGui, QtCore, uic
from PyQt4 import QtSql
from masterform import LlampexMasterForm
import time
import re
import qsqlrpcdriver.qtdriver as qtdriver
import threading
import traceback
from projectloader import LlampexTable
from qsqlmetadatamodel import QSqlMetadataModel, ItemComboDelegate

def h(*args): return os.path.realpath(os.path.join(os.path.dirname(os.path.abspath( __file__ )), *args))

class MyWidget(QtGui.QWidget):
    def setup(self):
        self.itemindex = None
        S = QtGui.QStyle
        self.option = QtGui.QStyleOptionViewItemV4()
        self.option.rect = QtCore.QRect(0,0,300,24)
        self.option.state = S.State_Active | S.State_Enabled
        self.delegate = QtGui.QStyledItemDelegate(self)
    
    def mouseDoubleClickEvent(self, event):
        S = QtGui.QStyle
        self.option.state |= S.State_Editing
        self.update()

    def sizeHint(self):
        if self.itemindex:
            return self.delegate.sizeHint(self.option, self.itemindex)
        else:
            sz = QtCore.QSize(120,24)
            return sz
        
    def setItemIndex(self, itemindex):
        self.itemindex = itemindex
        self.update()
        
    def paintEvent(self, pEvent):
        painter = QtGui.QPainter(self);
        if self.itemindex:
            self.delegate.paint(painter, self.option, self.itemindex)
        

class MasterScript(object):
    def __init__(self, form):
        self.form = form
        self.rpc = self.form.prjconn
        
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
            print "f0:", tmd.field[0]
            print "f1:", tmd.field[1]
            print "Nombre:", tmd.field.nombre
        except Exception, e:
            print "Error loading table metadata:"
            print traceback.format_exc()
        print
        table = self.form.ui.table
        
        table.setSortingEnabled( True )
        try:
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
            
            self.form.connect(tableheader, QtCore.SIGNAL("sortIndicatorChanged(int,Qt::SortOrder)"), self.table_sortIndicatorChanged)
            self.form.connect(tableheader, QtCore.SIGNAL("customContextMenuRequested(QPoint &)"),self.table_headerCustomContextMenuRequested)
            self.form.connect(action_addfilter, QtCore.SIGNAL("triggered(bool)"), self.action_addfilter_triggered)
            
        except Exception, e:
            print e
        
        
        self.form.connect(table, QtCore.SIGNAL("activated(QModelIndex)"),self.table_cellActivated)
        self.form.connect(table, QtCore.SIGNAL("clicked(QModelIndex)"),self.table_cellActivated)
        self.form.connect(self.form.ui.btnNew, QtCore.SIGNAL("clicked()"), self.btnNew_clicked)
        self.model = QSqlMetadataModel(None,self.db, tmd)
        self.model.decorations[None] = QtGui.QIcon(h("../../icons/null.png"))
        self.model.decorations[True] = QtGui.QIcon(h("../../icons/true.png"))
        self.model.decorations[False] = QtGui.QIcon(h("../../icons/false.png"))
        
        self.modelReady = threading.Event()
        self.modelSet = threading.Event()
        self.reload_data()
        self.select_data()
        self.settablemodel()
        self.mywidget = MyWidget(self.form.ui)
        self.mywidget.setup()
        layout = self.form.ui.layout()
        layout.addWidget(self.mywidget)
        
    def table_cellActivated(self, itemindex):
        print "Cell:", itemindex.row(), itemindex.column()
        self.mywidget.setItemIndex(itemindex)
    
    
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
        self.select_data()
    
    def table_headerCustomContextMenuRequested(self, point):
        print point
        
    def table_sortIndicatorChanged(self, column, order):
        print column, order
        
    def reload_data(self):
        self.model.setSort(0,0)
        
    def select_data(self):
        self.model.select()
    
    def settablemodel(self):
        self.form.ui.table.setModel(self.model)
        self.model.autoDelegate(self.form.ui.table)

            
        
