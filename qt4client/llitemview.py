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

class LlItemView1(QtGui.QAbstractItemView):
    def setup(self):
        self.colwidth = {}
        self.row = 0
        self.col = 0
        self.margin = (3,3,3,3)
        self.item = None
        self.persistentEditor = None
        self.setSizePolicy(QtGui.QSizePolicy.Preferred,QtGui.QSizePolicy.Minimum)
        self.setEditTriggers(QtGui.QAbstractItemView.DoubleClicked | QtGui.QAbstractItemView.EditKeyPressed)
        self.setSelectionMode(QtGui.QAbstractItemView.NoSelection)
        #self.viewport().setSizePolicy(QtGui.QSizePolicy.Preferred,QtGui.QSizePolicy.Minimum)
        #self.setTabKeyNavigation(False)

    def minimumSizeHint(self):
        w = self.colwidth.get(self.col, 50)
        sz = QtCore.QSize(w,16)
        return sz
        
    def setPosition(self,row, col):
        self.row = row
        self.col = col
        self.updatePosition()
    
    def setRow(self, row):
        self.row = row
        self.updatePosition()
    
    def setCol(self, col):
        self.col = col
        self.updatePosition()
        
    def focusInEvent(self, event):
        QtGui.QAbstractItemView.focusInEvent(self,event)
        if self.item and self.item.isValid():
            #print "focus IN:", self.row, self.col
            # TODO: Devuelve error si no se puede editar o si ya estaba editandose
            self.edit(self.item) 
            
    
    def focusOutEvent(self, event):
        QtGui.QAbstractItemView.focusOutEvent(self,event)
        #if self.item:
        #    #print "focus OUT:", self.row, self.col
    
    def updatePosition(self):
        model = self.model()
        if self.persistentEditor:
            self.closePersistentEditor(self.item)
        self.item = model.index(self.row, self.col)
        if not self.item.isValid():
            #print "Item invalid::"
            return False
        fnAutoDelegate = getattr(model, "autoDelegate", None)
        if fnAutoDelegate: fnAutoDelegate(self)
        smodel = self.selectionModel()
        smodel.setCurrentIndex(self.item, QtGui.QItemSelectionModel.NoUpdate);
        self.update()
        #self.openPersistentEditor(self.item)
        #self.persistentEditor = True
        #szh = self.sizeHint()
        #szh += QtCore.QSize(15,15)
        #self.resize(szh)
        return True
        
    def sizeHint(self):
        #sz = QtGui.QAbstractItemView.sizeHint(self)
        #sz.setHeight(32)
        w = self.colwidth.get(self.col, 50)
        sz = QtCore.QSize(w+32,32)
        return sz
        
        if self.item:
            sz = self.sizeHintForIndex(self.item)
        return sz
        
    def setColumnWidth(self, col, width):
        self.colwidth[col] = width
    """    
    def setDelegateForColumn(self, col, delegate):
        if col != self.col: return
        self.delegate = delegate
    """
    def paintEvent(self, pEvent):
        if not self.item: return
        if not self.item.isValid(): return
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
        delegate = self.itemDelegate(item)
        #painter.setClipRegion(QtGui.QRegion(option.rect))
        delegate.paint(painter, option, item)
        #painter.restore()
    
    # virtual QModelIndex	indexAt ( const QPoint & point ) const = 0        
    def indexAt(self, point):
        return self.item
        
    # virtual void	scrollTo ( const QModelIndex & index, ScrollHint hint = EnsureVisible ) = 0
    def scrollTo(self, index, hint):
        #print "scrollTo", index,hint
        return
        
    # virtual QRect	visualRect ( const QModelIndex & index ) const = 0
    def visualRect(self, index):
        if index != self.item: return QtCore.QRect()
        rect = self.rect()
        margin = self.margin
        rect.adjust(margin[0],margin[1],-margin[2],-margin[3])
        #szh = self.sizeHint()
        #print rect, szh
        
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
        w = None
        parent = None
        thisparent = self.parentWidget()
        smodel = self.selectionModel()
        selectedIndex = smodel.currentIndex()
        if not selectedIndex.isValid():
            if not self.updatePosition():
                # TODO: This is a patch to allow a future redraw when we're called in the middle of a Model Reset.
                QtCore.QTimer.singleShot(200,self.updatePosition)
            
            return self.item
        
        
        if cursorAction == QtGui.QAbstractItemView.MoveNext:
            w = self
            for i in range(10):
                w = w.nextInFocusChain()
                parent = w.parentWidget()
                if parent == thisparent: break
                
        elif cursorAction == QtGui.QAbstractItemView.MovePrevious:
            w = self
            for i in range(10):
                w = w.previousInFocusChain()
                parent = w.parentWidget()
                if parent == thisparent: break
        else:
            #print "moveCursor:", cursorAction, kbmodifiers
            pass
            
        if w:
            parent = w.parentWidget()
            #print "moveCursor, giving focus:", w.__class__.__name__
            #try: print w.row, w.col
            #except Exception, e: print e
            #print parent
            #print thisparent
            QtCore.QTimer.singleShot(50,w,QtCore.SLOT("setFocus()"))
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
        return QtGui.QRegion(self.visualRect(self.item))
