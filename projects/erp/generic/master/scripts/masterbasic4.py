# encoding: UTF-8
import os.path, traceback
from PyQt4 import QtGui, QtCore, uic
from PyQt4 import QtSql
from masterform import LlampexMasterForm
from recordform import loadActionFormRecord #LlampexRecordForm, LlampexQDialog
import time
import re
import qsqlrpcdriver.qtdriver as qtdriver
import threading
import traceback
from projectloader import LlampexTable
from qsqlmetadatamodel import QSqlMetadataModel, ItemComboDelegate
from llitemview import LlItemView1 as MyItemView
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
    def __init__(self, project, form):
        self.project = project
        self.form = form
        self.rpc = self.form.prjconn
        
        self.db = self.rpc.qtdb
        self.table = self.form.actionobj.table
        self.model = None
        self.row = None 
        self.col = None
        
        print
        try:
            tmd=LlampexTable.tableindex[self.table]
            self.tmd = tmd
            print tmd
            print "Code:", tmd.code
            print "Nombre:", tmd.name
            print "PKey:", tmd.primarykey
            print tmd.fieldlist
            print tmd.fields
            print "f0:", tmd.field[0]
            print "f1:", tmd.field[1]            
        except Exception, e:
            print "Error loading table metadata:"
            print traceback.format_exc()
        print
        table = self.form.ui.table
        
        table.setSortingEnabled( True )
        try:
            tableheader = table.horizontalHeader()
            tableheader.setSortIndicator(0,0)
            tableheader.setContextMenuPolicy( QtCore.Qt.CustomContextMenu )
            
            self.headerMenu = QtGui.QMenu(tableheader)
            
            action_addfilter = QtGui.QAction(
                        QtGui.QIcon(h("../../icons/page-zoom.png")),
                        "Add &Filter...", tableheader)
            action_showcolumns = QtGui.QAction(
                        QtGui.QIcon(h("../../icons/preferences-actions.png")), 
                        "Show/Hide &Columns...", tableheader)
            action_hidecolumn = QtGui.QAction("&Hide this Column", tableheader)
            action_addfilter.setIconVisibleInMenu(True)
            action_showcolumns.setIconVisibleInMenu(True)
            self.headerMenu.addAction(action_addfilter)
            self.headerMenu.addAction(action_showcolumns)
            self.headerMenu.addAction(action_hidecolumn)
            tableheader.setStretchLastSection(True)
            
            self.form.connect(tableheader, QtCore.SIGNAL("sortIndicatorChanged(int,Qt::SortOrder)"), self.table_sortIndicatorChanged)
            self.form.connect(tableheader, QtCore.SIGNAL("customContextMenuRequested(const QPoint&)"),self.table_headerCustomContextMenuRequested)
            self.form.connect(action_addfilter, QtCore.SIGNAL("triggered(bool)"), self.action_addfilter_triggered)
            self.form.connect(action_hidecolumn, QtCore.SIGNAL("triggered(bool)"), self.action_hidecolumn_triggered)
            
        except Exception, e:
            print e
        
        # set search invisible
        self.form.ui.searchFrame.setVisible(False)
        
        self.form.connect(table, QtCore.SIGNAL("activated(QModelIndex)"),self.table_cellActivated)
        self.form.connect(table, QtCore.SIGNAL("clicked(QModelIndex)"),self.table_cellActivated)
        self.form.connect(self.form.ui.btnNew, QtCore.SIGNAL("clicked()"), self.btnNew_clicked)
        self.form.connect(self.form.ui.btnEdit, QtCore.SIGNAL("clicked()"), self.btnEdit_clicked)
        self.form.connect(self.form.ui.btnBrowse, QtCore.SIGNAL("clicked()"), self.btnBrowse_clicked)
        self.form.connect(self.form.ui.searchBox, QtCore.SIGNAL("textChanged(const QString&)"), self.searchBox_changed)
        self.form.connect(self.form.ui.searchCombo, QtCore.SIGNAL("currentIndexChanged(const QString&)"), self.searchCombo_changed)
        self.model = QSqlMetadataModel(None,self.db, tmd)
        self.model.decorations[None] = QtGui.QIcon(h("../../icons/null.png"))
        self.model.decorations[True] = QtGui.QIcon(h("../../icons/true.png"))
        self.model.decorations[False] = QtGui.QIcon(h("../../icons/false.png"))
        
        # Add fields to combobox
        self.form.ui.searchCombo.addItems(self.model.getHeaderAlias())
        
        self.modelReady = threading.Event()
        self.modelSet = threading.Event()
        self.reload_data()
        self.select_data()
        self.settablemodel()
        """
        layout = self.form.ui.layout()

        self.fieldlayout = QtGui.QHBoxLayout()
        self.fieldlayout.setSpacing(1)
        
        self.fieldviews = []
        
        for i, name in enumerate(self.tmd.fieldlist):
        
            myitemview = MyItemView(self.form.ui)
            myitemview.setup()
            myitemview.setModel(self.model)
            myitemview.setCol(i)
        
            self.fieldlayout.addWidget(myitemview)
            self.fieldviews.append(myitemview)

        layout.addLayout( self.fieldlayout )
        """
        
    def table_cellActivated(self, itemindex):
        self.row, self.col = itemindex.row(), itemindex.column()
        print "Cell:", self.row, self.col
        """
        for fieldview in self.fieldviews:
            fieldview.setRow(self.row)        
        """
        
    def btnNew_clicked(self):
        print "Button New clicked"
        load = loadActionFormRecord(self.project, self.form, 'INSERT', self.form.actionobj, self.rpc, self.tmd, self.model, self.row)
        """
        print "Button New clicked"
        dialog = QtGui.QDialog(self.form)
        dialog.setWindowTitle("Insert new record")
        ret = dialog.exec_()
        print ret
        """
    def btnEdit_clicked(self):
        print "Button Edit clicked --> Row: ", self.row
        load = loadActionFormRecord(self.project, self.form, 'EDIT', self.form.actionobj, self.rpc, self.tmd, self.model, self.row)        
        
    def btnBrowse_clicked(self):
        print "Button Browse clicked"
        #change visibility of searchFrame
        self.form.ui.searchFrame.setVisible(not self.form.ui.searchFrame.isVisible())
        
    def searchBox_changed(self,text):
        print "Search Box changed to ", unicode(text)
        self.model.setBasicFilter(self.form.ui.searchCombo.currentText(),text)
        self.model.refresh()
    
    def searchCombo_changed(self,alias):
        print "Search Combo changed to ", unicode(alias)
        self.model.setBasicFilter(alias,self.form.ui.searchBox.text())
        self.model.refresh()
    
    def action_addfilter_triggered(self, checked):
        print "Add Filter triggered:", checked
        rettext, ok = QtGui.QInputDialog.getText(self.form, "Add New Filter",
            "Write New WHERE expression:", QtGui.QLineEdit.Normal, self.model.getFilter())
        if ok:
            self.form.ui.searchBox.setText("")
            self.model.setFilter(rettext)
            self.model.refresh()
            
    def action_hidecolumn_triggered(self, checked):
        print "Hide Column triggered:", checked
        self.model.tmd.fieldlist.pop(self.lastColumnClicked)
        self.model.refresh()
        self.form.ui.searchCombo.clear()
        self.form.ui.searchCombo.addItems(self.model.getHeaderAlias())
    
    def table_headerCustomContextMenuRequested(self, pos):
        print pos
        self.lastColumnClicked = self.form.ui.table.horizontalHeader().logicalIndexAt(pos)
        print "We are in column: " + str(self.lastColumnClicked)
        self.headerMenu.exec_( self.form.ui.table.horizontalHeader().mapToGlobal(pos) )
        
    def table_sortIndicatorChanged(self, column, order):
        print column, order
        self.model.setSort(column,order)
        self.model.refresh()
        
    def reload_data(self):
        self.model.setSort(0,0)
        
    def select_data(self):
        self.model.select()
    
    def settablemodel(self):
        self.form.ui.table.setModel(self.model)
        self.model.autoDelegate(self.form.ui.table)
