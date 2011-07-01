#!/usr/bin/env python
# encoding: UTF-8

import os.path

import sys
from PyQt4 import QtGui, QtCore, uic, QtSql

class ItemComboDelegate(QtGui.QItemDelegate):
    def __init__(self,*args):
        QtGui.QItemDelegate.__init__(self,*args)
        self.items = []
        self.values = []
        
    def createEditor(self, parent, option, index):
        combo = QtGui.QComboBox(parent)
        for item in self.items:
            combo.addItem(item)
        return combo
        
    def setEditorData(self, editor, index):
        model = index.model()
        val = model.data(index, QtCore.Qt.EditRole)
        idx = self.values.index(val)
        editor.setCurrentIndex(idx)
    
    def setModelData(self, editor, model, index):
        idx = editor.currentIndex()
        val = self.values[idx]
        model.setData(index,val, QtCore.Qt.EditRole)        
        
        

class QSqlMetadataModel(QtSql.QSqlQueryModel):
    colors = {}
    brushes = {}
    
    @classmethod
    def getColor(self, color):
        if color not in self.colors: 
            self.colors[color] = QtGui.QColor(color)
        return self.colors[color]
        
    @classmethod
    def getBrush(self, color):
        if color not in self.brushes: 
            self.brushes[color] = QtGui.QBrush(self.getColor(color))
        return self.brushes[color]
    
    def __init__(self, parent, db, tmd = None):
        QtSql.QSqlQueryModel.__init__(self, parent)
        self.db = db
        self.tmd = None
        self.checkstate = {}
        self.decorations = {}
        if tmd: self.setMetaData(tmd)
        
    def setMetaData(self,tmd):
        assert(self.tmd is None)
        self.tmd = tmd
        self.table = self.tmd.code
        self.pk = self.tmd.primarykey
        self.fieldlist = self.tmd.fieldlist
        self.pkidx = self.tmd.fieldlist.index(self.pk)
    
    def filter(self):
        return ""
    
    def setFilter(self):
        pass
    
    def setSort(self, col, desc):
        # sorts column col ascending, or descending if desc == True
        pass
    
    def flags(self, index):
        assert(self.tmd)
        flags = 0
        field = self.tmd.field[index.column()]
        if field.get("tableSelectable", True):
            flags |= QtCore.Qt.ItemIsSelectable
        if field.get("tableEditable", False):
            flags |= QtCore.Qt.ItemIsEditable
        if field.get("tableCheckable", False):
            flags |= QtCore.Qt.ItemIsUserCheckable
        if field.get("tableTristate", False):
            flags |= QtCore.Qt.ItemIsTristate
        if field.get("tableEnabled", True):
            flags |= QtCore.Qt.ItemIsEnabled
            
        return flags
    
    def colType(self, column):
        try: column = column.column()
        except Exception: pass
        field = self.tmd.field[column]
        ftype = field.get("type", "vchar")
        if ftype == "bool": return "b"
        if ftype == "date": return "d"
        if ftype == "datetime": return "dt"
        if ftype == "double": return "n"
        if ftype == "float": return "n"
        if ftype == "int": return "n"
        if ftype.startswith("number"): return "n"
        if ftype == "string" or ftype.startswith("vchar"): return "s"
        if ftype == "time": return "t"
        return "x"
        
    def autoDelegate(self, itemview):
        delegate_bool = ItemComboDelegate(itemview)
        delegate_bool.items = [u"Sí",u"No",u"--"]
        delegate_bool.values = [True,False,None]
        fnSetColumnWidth = getattr(itemview,"setColumnWidth",None)
        for i, name in enumerate(self.tmd.fieldlist):
            field = self.tmd.field[i]
            ctype = self.colType(i)
            delegate = None
            optionlist = field.get("optionlist",None)
            valuelist = field.get("valuelist",optionlist)
            
            if ctype == "b": delegate = delegate_bool
            if optionlist:
                delegate_adhoc = ItemComboDelegate(itemview)
                delegate_adhoc.items = valuelist
                delegate_adhoc.values = optionlist
                delegate = delegate_adhoc
                
            if delegate:
                itemview.setItemDelegateForColumn(i, delegate)   
            widths = [50]
            for row in range(min(20, self.rowCount())):
                midx = self.index(row,i)
                sz = itemview.sizeHintForIndex(midx)
                widths.append(sz.width())
            widths.sort()
            x = len(widths) / 2
            m = widths[x:]
            lm = len(m)
            w = sum(m) / lm + 25
            #w = itemview.sizeHintForColumn(i)
            fnSetColumnWidth(i, w)
            
        
        
            
    def data(self, index, role = None):
        if role is None: role = QtCore.Qt.DisplayRole
        if role == QtCore.Qt.DecorationRole:
            ret = QtSql.QSqlQueryModel.data(self,index,QtCore.Qt.DisplayRole)
            field = self.tmd.field[index.column()]
            ftype = field.get("type", "vchar")
            k = None
            if ret.isNull(): k = "null"
            else:
                if ftype == "bool": 
                    ret = ret.toBool()
                    if bool(ret): k = "true"
                    else: k = "false"
            decoration = self.decorations.get(k)
            if decoration: return decoration
            
            
        if role == QtCore.Qt.BackgroundRole:
            row = index.row()
            c = self.checkstate.get( (row,0), 0)
            if c == 2:
                return self.getBrush("#FB9")
            elif c == 1:
                return self.getBrush("#FEA")
            
        elif role == QtCore.Qt.ForegroundRole:
            ret = self.data(index,QtCore.Qt.EditRole)
            ctype = self.colType(index)
            field = self.tmd.field[index.column()]
            optionlist = field.get("optionlist",None)
            colorlist = field.get("colorlist",None)
            if not optionlist:
                if ctype == "b": 
                    optionlist = [True,False,None]
                    colorlist = ["#0B0","#B00","#644"]
            elif not colorlist:
                colorlist = [ None for x in optionlist ]
                
            brush = None
            if optionlist and colorlist:
                idx = optionlist.index(ret)
                if idx >= 0: color = colorlist[idx]
                if color: brush = self.getBrush(color)
                
                
            if brush is None:
                if ctype == "n": 
                    if float(ret) < 0: brush = self.getBrush("#B00")
            if brush is not None:
                return brush
            
            # # return self.brush_black
        if role == QtCore.Qt.CheckStateRole: 
            field = self.tmd.field[index.column()]
            if field.get("tableCheckable", False):
                k = (index.row(), index.column())
                return self.checkstate.get(k,QtCore.Qt.Unchecked)
                
        if role in (QtCore.Qt.EditRole, QtCore.Qt.DisplayRole): 
            ret = QtSql.QSqlQueryModel.data(self,index,role)
            field = self.tmd.field[index.column()]
            ftype = field.get("type", "vchar")
            optionlist = field.get("optionlist",None)
            valuelist = field.get("valuelist",optionlist)
            if not optionlist:
                if ftype == "bool": 
                    optionlist = [True,False,None]
                    valuelist = [u"Sí",u"No","--"]
            if ret.isNull(): ret = None
            else:
                try:            
                    if ftype == "bool": ret = ret.toBool()
                    if ftype == "date": ret = ret.toDate()
                    if ftype == "datetime": ret = ret.toDateTime()
                    if ftype == "double": ret, ok = ret.toDouble()
                    if ftype == "float": ret, ok = ret.toDouble()
                    if ftype.startswith("number"): ret, ok = ret.toDouble()
                    if ftype == "int": ret, ok = ret.toInt()
                    if ftype == "string" or ftype.startswith("vchar"): ret = ret.toString()
                    if ftype == "time": ret = ret.toTime()
                except ValueError: 
                    ret = None
            
            if role == QtCore.Qt.DisplayRole and optionlist:
                idx = optionlist.index(ret)
                if idx >= 0: ret = valuelist[idx]
            
            return ret
        return QtSql.QSqlQueryModel.data(self,index,role)
    
    def setData(self, index, value, role):
        if value == self.data(index, role): return False
        if role == QtCore.Qt.EditRole:
            primaryKeyIndex = self.index(index.row(), self.pkidx)
            pkeyval = self.data(primaryKeyIndex)

            self.clear()
            try:
                return self.setValue(pkeyval, self.tmd.field[index.column()]['name'], value)
            finally:
                self.refresh()
        elif role == QtCore.Qt.CheckStateRole:
            k = (index.row(), index.column())
            val, ok = value.toInt()
            print "Check %s -> %s" % (repr(k), repr(val))
            c = self.checkstate.get(k,0) 
            if c == 0: val = 1
            self.checkstate[k]=val
            row = index.row()
            model = index.model()
            columns = model.columnCount()
            left = model.index(row,0)
            right = model.index(row,columns-1)
            
            self.emit(QtCore.SIGNAL("dataChanged(QModelIndex,QModelIndex)"), left,right)
            return True
        return False
    
    def setValue(self, pkvalue, field, value):
        query = QtSql.QSqlQuery(self.db)
        query.prepare("UPDATE %(table)s SET %(field)s = ? WHERE %(pk)s = ?" %
                    {
                        'table' : self.table,
                        'field' : str(field),
                        'pk' : self.pk,
                    })
        query.addBindValue(value)
        query.addBindValue(pkvalue)
        return query.exec_()

    def refresh(self):
        self.setQuery('select %s from %s order by %s' % (", ".join(self.tmd.fieldlist), self.table, self.pk )  , self.db)
        for i, fname in enumerate(self.tmd.fieldlist):
            field = self.tmd.field[i]
            self.setHeaderData(i, QtCore.Qt.Horizontal, field['alias'])
    select = refresh
    