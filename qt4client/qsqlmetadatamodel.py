#!/usr/bin/env python
# encoding: UTF-8

import os.path

import sys
from PyQt4 import QtGui, QtCore, uic, QtSql

class QSqlMetadataModel(QtSql.QSqlQueryModel):
    color_red = QtGui.QColor(255,0,0)
    color_green = QtGui.QColor(0,200,0)
    color_blue = QtGui.QColor(0,0,255)
    color_black = QtGui.QColor(0,0,0)
    brush_red = QtGui.QBrush(color_red)
    brush_green = QtGui.QBrush(color_green)
    brush_blue = QtGui.QBrush(color_blue)
    brush_black = QtGui.QBrush(color_black)
    color_beige = QtGui.QColor(245,255,190)
    brush_beige = QtGui.QBrush(color_beige)
    
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
        if field.get("tableEnabled", True):
            flags |= QtCore.Qt.ItemIsEnabled
            
        return flags
    
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
            if self.checkstate.get( (row,0), False):
                return self.brush_beige
            
        elif role == QtCore.Qt.ForegroundRole:
            ret = QtSql.QSqlQueryModel.data(self,index,QtCore.Qt.DisplayRole)
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
                if ftype == "double": ret, ok = ret.toDouble()
                if ftype == "float": 
                    ret, ok = ret.toDouble()
                    if float(ret) < 0: return self.brush_red
                if ftype == "int": 
                    ret, ok = ret.toInt()
                    if float(ret) < 0: return self.brush_red
                if ftype == "string" or ftype.startswith("vchar"): ret = ret.toString()
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
            if role == QtCore.Qt.DisplayRole and ret.isNull(): return None
            try:            
                if ftype == "bool": 
                    ret = ret.toBool()
                    if role == QtCore.Qt.DisplayRole:
                        ret = u"Sí" if ret else u"No"
                if ftype == "date": ret = ret.toDate()
                if ftype == "datetime": ret = ret.toDateTime()
                if ftype == "double": ret, ok = ret.toDouble()
                if ftype == "float": ret, ok = ret.toDouble()
                if ftype == "int": ret, ok = ret.toInt()
                if ftype == "string" or ftype.startswith("vchar"): ret = ret.toString()
                if ftype == "time": ret = ret.toTime()
            except ValueError: 
                ret = None
            
            return ret
        return QtSql.QSqlQueryModel.data(self,index,role)
    
    def setData(self, index, value, role):
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
            self.checkstate[k]=val
            self.emit(QtCore.SIGNAL("dataChanged"), index,index)
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
    