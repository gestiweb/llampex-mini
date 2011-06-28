#!/usr/bin/env python
# encoding: UTF-8

import os.path

import sys
from PyQt4 import QtGui, QtCore, uic, QtSql

class QSqlMetadataModel(QtSql.QSqlQueryModel):
    def __init__(self, db, tmd = None):
        QtSql.QSqlQueryModel.__init__(self)
        self.db = db
        if tmd: self.setMetaData(tmd)
        
    def setMetaData(self,tmd):
        try:
            assert (self.tmd is None)
            self.tmd = tmd
        except Exception, e:
            print "Error loading table metadata:", e
        
    
    def flags(self, index):
        flags = 0
        assert (self.tmd)
        field = self.mtd.fields[index.column()]
        if field.get("tableSelectable", True):
            flags |= QtCore.Qt.ItemIsSelectable
        if field.get("tableEditable", False):
            flags |= QtCore.Qt.ItemIsEditable
        if field.get("tableCheckable", False):
            flags |= QtCore.Qt.ItemIsCheckable
        if field.get("tableEnabled", True):
            flags |= QtCore.Qt.ItemIsEnabled
            
        return flags
    
    def setData(self, index, value, role):
        #if index.column() == 0:
        #    return False

        primaryKeyIndex = self.index(index.row(), 0)
        id = self.data(primaryKeyIndex)

        self.clear()

        if index.column() == 1:
            ok = self.setValue(id, "username", value)
        elif index.column() == 2:
            ok = self.setValue(id, "password", value)
        elif index.column() == 3:
            ok = self.setValue(id, "active", value)
        else:
            ok = self.setValue(id, "admin", value)

        self.refresh()
        return ok
    
    def setValue(self, id, field, value):
        query = QtSql.QSqlQuery(self.db)
        query.prepare('update users set '+field+' = ? where id = ?')
        query.addBindValue(value)
        query.addBindValue(id)
        return query.exec_()

    def refresh(self):
        self.setQuery('select * from '+self.table,self.db)
        self.setHeaderData(0, QtCore.Qt.Horizontal, "ID")
        self.setHeaderData(1, QtCore.Qt.Horizontal, "Username")
        self.setHeaderData(2, QtCore.Qt.Horizontal, "Password")
        self.setHeaderData(3, QtCore.Qt.Horizontal, "Active")
        self.setHeaderData(4, QtCore.Qt.Horizontal, "Admin")

    