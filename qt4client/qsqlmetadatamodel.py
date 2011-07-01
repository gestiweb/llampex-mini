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
    color_red = QtGui.QColor(255,0,0)
    color_green = QtGui.QColor(0,200,0)
    color_blue = QtGui.QColor(0,0,255)
    color_black = QtGui.QColor(0,0,0)
    brush_red = QtGui.QBrush(color_red)
    brush_green = QtGui.QBrush(color_green)
    brush_blue = QtGui.QBrush(color_blue)
    brush_black = QtGui.QBrush(color_black)
    color_beige = QtGui.QColor(255,245,190)
    brush_beige = QtGui.QBrush(color_beige)
    
    color_beige2 = QtGui.QColor(255,225,180)
    brush_beige2 = QtGui.QBrush(color_beige2)
    
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
            ctype = self.colType(i)
            delegate = None
            if ctype == "b": delegate = delegate_bool
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
                return self.brush_beige2
            elif c == 1:
                return self.brush_beige
            
        elif role == QtCore.Qt.ForegroundRole:
            ret = QtSql.QSqlQueryModel.data(self,index,QtCore.Qt.DisplayRole)
            ctype = self.colType(index)
            field = self.tmd.field[index.column()]
            ftype = field.get("type", "vchar")
            if role == QtCore.Qt.DisplayRole and ret.isNull(): return None
            try:            
                if ftype == "bool": 
                    ret = ret.toBool()
                    if bool(ret): 
                        return self.brush_green
                    else:
                        return self.brush_red
                        
                if ftype == "date": ret = ret.toDate()
                if ftype == "datetime": ret = ret.toDateTime()
                
                if ctype == "n": 
                    ret, ok = ret.toDouble()
                    if float(ret) < 0: return self.brush_red
                    
                if ctype == "s": ret = ret.toString()
                if ftype == "time": ret = ret.toTime()
            except ValueError: 
                ret = None
            
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
            if ret.isNull(): return None
            try:            
                if ftype == "bool": 
                    ret = ret.toBool()
                    if role == QtCore.Qt.DisplayRole:
                        ret = u"Sí" if ret else u"No"
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
    