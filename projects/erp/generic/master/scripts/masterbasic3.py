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

class MyItemView(QtGui.QAbstractItemView):
    def setup(self):
        print "setup"
        self.row = 0
        self.col = 0
        self.margin = (5,5,5,5)
        self.item = None
        self.delegate = QtGui.QStyledItemDelegate(self)
        self.setSizePolicy(QtGui.QSizePolicy.Preferred,QtGui.QSizePolicy.Minimum)
    
    def setDelegate(self, delegate):
        self.delegate = delegate
    
    def setPosition(self,row, col):
        self.row = row
        self.col = col
        model = self.model()
        self.item = model.index(self.row, self.col)
        fnAutoDelegate = getattr(model, "autoDelegate", None)
        if fnAutoDelegate: fnAutoDelegate(self)
        
    def sizeHint(self):
        #sz = QtGui.QAbstractItemView.sizeHint(self)
        #sz.setHeight(32)
        sz = None
        if self.item:
            sz = self.sizeHintForIndex(self.item)
        else:
            sz = QtCore.QSize(120,16)
        return sz
    
    def setDelegateForColumn(self, col, delegate):
        if col != self.col: return
        self.delegate = delegate
    
    def paintEvent(self, pEvent):
        if not self.item: return
        S = QtGui.QStyle
        
        focus = self.hasFocus()
        viewstate = self.state()
        option = self.viewOptions()
        state = option.state
        enabled = bool(state & S.State_Enabled)
        
        item = self.item # Element to be drawn
        if focus:
            option.state |= S.State_HasFocus
            if viewstate & S.State_Editing:
                option.state |= S.State_Editing
        
        if viewstate & S.State_MouseOver:
            option.state |= S.State_MouseOver
        else:
            option.state &= ~S.State_MouseOver
        painter = QtGui.QStylePainter(self.viewport())
        option.rect = self.visualRect(item)
        #painter.save()
        
        #painter.setClipRegion(QtGui.QRegion(option.rect))
        self.delegate.paint(painter, option, item)
        #painter.restore()
            
            
    
    # virtual QModelIndex	indexAt ( const QPoint & point ) const = 0        
    def indexAt(self, point):
        return self.item
        
    # virtual void	scrollTo ( const QModelIndex & index, ScrollHint hint = EnsureVisible ) = 0
    def scrollTo(self, index, hint):
        return
        
    # virtual QRect	visualRect ( const QModelIndex & index ) const = 0
    def visualRect(self, index):
        rect = self.rect()
        margin = self.margin
        rect.adjust(margin[0],margin[1],-margin[2],-margin[3])
        return rect 
    
    
    # *** PROTECTED *** / INTERNAL FUNCTIONS::
    
    # virtual int	horizontalOffset () const = 0
    def horizontalOffset(self):
        "Returns the horizontal offset of the view"
        return int(self.col)
    
    # virtual int	verticalOffset () const = 0
    def verticalOffset(self):
        "Returns the vertical offset of the view"
        return int(self.row)
        
    # virtual bool	isIndexHidden ( const QModelIndex & index ) const = 0
    def isIndexHidden(self, index):
        """ 
        Returns true if the item referred to by the given index is hidden 
        in the view, otherwise returns false.
        Hiding is a view specific feature. For example in TableView a column 
        can be marked as hidden or a row in the TreeView.
        """
        row = index.row()
        col = index.col()
        if (row,col) == (self.row, self.col): return True
        else: return False
    
    # virtual QModelIndex	moveCursor ( CursorAction cursorAction, Qt::KeyboardModifiers modifiers ) = 0
    def moveCursor(self, cursorAction, kbmodifiers):
        """
        Returns a QModelIndex object pointing to the next object in the 
        view, based on the given cursorAction and keyboard modifiers 
        specified by modifiers.
        """
        return self.item
        
    # virtual void	setSelection ( const QRect & rect, QItemSelectionModel::SelectionFlags flags ) = 0
    def setSelection(self, rect, flags):
        """
        Applies the selection flags to the items in or touched by 
        the rectangle, rect.
        When implementing your own itemview setSelection should 
        call selectionModel()->select(selection, flags) where selection 
        is either an empty QModelIndex or a QItemSelection that contains 
        all items that are contained in rect.
        """
        # Does nothing.
        return 

    # virtual QRegion	visualRegionForSelection ( const QItemSelection & selection ) const = 0
    def visualRegionForSelection(self, selection):
        """
        Returns the region from the viewport of the items in the given selection.
        """
        # TODO: Implementar esta funcion ?
        return
        
        
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
        layout = self.form.ui.layout()

        
        self.fieldlayout = QtGui.QHBoxLayout()
        
        self.myitemview = MyItemView(self.form.ui)
        self.myitemview.setup()
        self.myitemview.setModel(self.model)
        self.myitemview.setPosition(0,0)
        
        self.fieldlayout.addWidget(self.myitemview)

        layout.addLayout( self.fieldlayout )
        
        
    def table_cellActivated(self, itemindex):
        print "Cell:", itemindex.row(), itemindex.column()
        self.myitemview.setPosition(itemindex.row(), itemindex.column())
        
    
    
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
        print "table_headerCustomContextMenuRequested" , point
        
    def table_sortIndicatorChanged(self, column, order):
        print "table_sortIndicatorChanged", column, order
        
    def reload_data(self):
        self.model.setSort(0,0)
        
    def select_data(self):
        self.model.select()
    
    def settablemodel(self):
        self.form.ui.table.setModel(self.model)
        self.model.autoDelegate(self.form.ui.table)

            
        
