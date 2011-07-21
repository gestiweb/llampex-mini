#!/usr/bin/env python
# encoding: UTF-8
import random
import os.path
from datetime import datetime, date
import sys
from PyQt4 import QtGui, QtCore, uic, QtSql

QtFormatRole = QtCore.Qt.UserRole + 1

class utilities():
    def __init__(self):
        self.colors = {}
        self.brushes = {}
    
    def getColor(self, color):
        if color not in self.colors: 
            self.colors[color] = QtGui.QColor(color)
        return self.colors[color]
        
    def getBrush(self, color):
        if color not in self.brushes: 
            self.brushes[color] = QtGui.QBrush(self.getColor(color))
        return self.brushes[color]
    


def autoDelegateMetadata(self, itemview):
    delegate_bool = ItemComboDelegate(itemview)
    delegate_bool.items = [u"Sí",u"No",u"--"]
    delegate_bool.values = [True,False,None]
    basic_delegate = ItemBasicDelegate(itemview)
    fnSetColumnWidth = getattr(itemview,"setColumnWidth",None)
    for i, name in enumerate(self.tmd.fieldlist):
        field = self.tmd.field[i]
        ctype = self.colType(i)
        delegate = basic_delegate
        optionlist = field.get("optionlist",None)
        valuelist = field.get("valuelist",optionlist)            
        if valuelist: 
            # This is to avoid the same data in optionlist being referenced
            # in valuelist instead of being copied.
            valuelist = valuelist[:]
        
        if ctype == "b": delegate = delegate_bool
        if optionlist:
            delegate_adhoc = ItemComboDelegate(itemview)
            delegate_adhoc.items = valuelist
            delegate_adhoc.values = optionlist
            delegate = delegate_adhoc

        if delegate:
            itemview.setItemDelegateForColumn(i, delegate)   
        if fnSetColumnWidth:
            if i not in self.columnWidth:
                widths = [50]
                for row in range(min(20, self.rowCount())):
                    midx = self.index(row,i)
                    sz = itemview.sizeHintForIndex(midx)
                    widths.append(sz.width())
                widths.sort()
                x = len(widths) / 4 + 1
                m = widths[x:]
                lm = len(m) 
                if lm:
                    w = sum(m) / lm + 10
                    #w = itemview.sizeHintForColumn(i)
                    self.columnWidth[i] = w
                else:
                    self.columnWidth[i] = None
            w = self.columnWidth[i]
            if w:
                fnSetColumnWidth(i, w)
        

class ItemComboDelegate(QtGui.QStyledItemDelegate):
    def __init__(self,*args):
        QtGui.QItemDelegate.__init__(self,*args)
        self.items = []
        self.values = []
        
    def createEditor(self, parent, option, index):
        combo = QtGui.QComboBox(parent)
        #combo.setWindowFlags(QtCore.Qt.Popup | QtCore.Qt.FramelessWindowHint)
        for item in self.items:
            if item: combo.addItem(item)
        return combo
        
    def setEditorData(self, editor, index):
        model = index.model()
        val = model.data(index, QtCore.Qt.EditRole)
        idx = None
        try: 
            if val: idx = self.values.index(val)
        except ValueError:
            if val:
                self.items.append(val) 
                self.values.append(val) 
                editor.addItem(val)
                idx = self.values.index(val)
            
        if idx: editor.setCurrentIndex(idx)
    
    def setModelData(self, editor, model, index):
        idx = editor.currentIndex()
        val = self.values[idx]
        model.setData(index,val, QtCore.Qt.EditRole)        
        

class ItemBasicDelegate(QtGui.QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        widget = QtGui.QStyledItemDelegate.createEditor(self, parent, option, index)
        if isinstance(widget, (QtGui.QDateEdit,QtGui.QDateTimeEdit)):
            widget.setCalendarPopup(True)
            model = index.model()
            format = model.data(index, QtFormatRole)
            if format:
                # TODO: asignar el formato al widget
                widget.setDisplayFormat(format);
        try:
            widget.setFrame(True)
        except AttributeError, e:
            pass
        return widget
    
    def updateEditorGeometry(self, widget, option, index):
        #QtGui.QStyledItemDelegate.updateEditorGeometry(self, widget, option, index)
        widget.setGeometry(option.rect)
        #print widget.frameGeometry(), widget.contentsRect()
        
        #widget.setWindowFlags(QtCore.Qt.Popup)
        #widget.setWindowFlags(QtCore.Qt.Popup | QtCore.Qt.FramelessWindowHint)
        """
        if isinstance(widget, (QtGui.QDateEdit,QtGui.QDateTimeEdit)):
            w,h = widget.width(), widget.height()
            widget.resize(w-15,h)
        """ 
                

class QMetadataModel(QtSql.QSqlQueryModel):
    def __init__(self, parent, db, tmd = None):
        QtSql.QSqlQueryModel.__init__(self, parent)
        self.db = db
        self.tmd = tmd
        self.table = self.tmd.code
        self.fieldlist = self.tmd.fieldlist
        self.pk = self.tmd.primarykey
        self.pkidx = self.tmd.fieldlist.index(self.pk)
        self.columnWidth = {}
        self.checkstate = {}
        self.decorations = {}
        self.dirtyrows = {}
        self.rows = 1
        self._header_data = {}
        
        self.utilities = utilities()
        
        for i, fname in enumerate(self.tmd.fieldlist):
            field = self.tmd.field[i]
            self.setHeaderData(i, QtCore.Qt.Horizontal, field['alias'])
            if i % 2 == 0:
                color = self.utilities.getBrush("#00A")
            else:
                color = self.utilities.getBrush("#090")
            self.setHeaderData(i, QtCore.Qt.Horizontal, color, role = QtCore.Qt.ForegroundRole)

        
    def getHeaderAlias(self):
        header = []
        for i, fname in enumerate(self.tmd.fieldlist):
            field = self.tmd.field[i]
            header.append(field['alias'])
        return header
    
    def setSort(self, column, order):
        pass
    
    def setBasicFilter(self, fieldname, filtertext):
        pass
    
    def setFilter(self, filtertext):
        pass
    
    def select(self):
        pass
    
    def refresh(self):
        pass

    def flags(self, index):
        assert(self.tmd)
        flags = 0
        field = self.tmd.field[index.column()]
        if field.get("tableSelectable", True):
            flags |= QtCore.Qt.ItemIsSelectable
        if field.get("tableEditable", True):
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
        
    autoDelegate = autoDelegateMetadata    
        
    def columnCount(self, parent = None):
        if parent is None: parent = QtCore.QModelIndex()
        if parent.isValid(): raise ValueError, "Valid parent passed to columnCount"
        return len(self.tmd.fieldlist)
    
    def rowCount(self, parent = None):
        if parent is None: parent = QtCore.QModelIndex()
        if parent.isValid(): raise ValueError, "Valid parent passed to rowCount"
        return self.rows
        
    def setHeaderData(self, section, orientation, value, role = None):
        if role == None: role = QtCore.Qt.DisplayRole
        k = section, orientation, role
        self._header_data[k] = QtCore.QVariant(value)
    
    def headerData(self, section, orientation, role):
        k = section, orientation, role
        return self._header_data.get(k, QtCore.QAbstractTableModel.headerData(self, section, orientation, role))
        
        #if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
        #    i = section
        #    field = self.tmd.field[i]
        #    return field['alias']
    
    def data(self, index, role = None):
        field = self.tmd.field[index.column()]
        ctype = self.colType(index)
        
        if role is None: role = QtCore.Qt.DisplayRole
        if role == QtFormatRole:
            # TODO: Si tiene formato devolverlo como string
            # ... en caso contrario devolver None.
            format = field.get("format", None)
            return format
        
        elif role == QtCore.Qt.DecorationRole:
            ret = self.data(index,QtCore.Qt.EditRole)
            optionlist = field.get("optionlist",None)
            iconlist = field.get("iconlist",None)
            icon = None
            decoration = None
            if not optionlist:
                if ctype == "b": 
                    optionlist = [True,False,None]
            if not iconlist and optionlist:
                    iconlist = optionlist

            if optionlist and iconlist:
                try:
                    idx = optionlist.index(ret)
                except ValueError:
                    idx = -1
                if idx >= 0: 
                    icon = iconlist[idx]
                    decoration = self.decorations.get(icon)
                if decoration: return decoration
            
        elif role == QtCore.Qt.TextAlignmentRole:            
            if ctype == "n":
                return QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter
                
        elif role == QtCore.Qt.BackgroundRole:
            row = index.row()
            if row in self.dirtyrows:
                return self.utilities.getBrush("#EEE")
            c = self.checkstate.get( (row,0), 0)
            if c == 2:
                return self.utilities.getBrush("#FB9")
            elif c == 1:
                return self.utilities.getBrush("#FEA")
            
        elif role == QtCore.Qt.ForegroundRole:
            ret = self.data(index,QtCore.Qt.EditRole)
            optionlist = field.get("optionlist",None)
            colorlist = field.get("colorlist",None)
            color = None
            if not optionlist:
                if ctype == "b": 
                    optionlist = [True,False,None]
                    colorlist = ["#0B0","#B00","#644"]
            elif not colorlist:
                colorlist = [ None for x in optionlist ]
                
            brush = None
            if optionlist and colorlist:
                try: idx = optionlist.index(ret)
                except ValueError: idx = -1
                try:
                    if idx >= 0: color = colorlist[idx]
                    if color: brush = self.utilities.getBrush(color)
                except IndexError:
                    pass
                
            if brush is None:
                if ctype == "n": 
                    if ret is None: brush = self.utilities.getBrush("#00B")
                    elif float(ret) < 0: brush = self.utilities.getBrush("#B00")
            if brush is not None:
                return brush

        if role == QtCore.Qt.CheckStateRole: 
            if field.get("tableCheckable", False):
                k = (index.row(), index.column())
                return self.checkstate.get(k,QtCore.Qt.Unchecked)
                    
        if role in (QtCore.Qt.EditRole, QtCore.Qt.DisplayRole):
            row = index.row()
            col = index.column()
            ret = None
            if row in self.dirtyrows:
                if col in self.dirtyrows[row]:
                    ret = self.dirtyrows[row][col]
            
            if ret is None:
                ret = QtSql.QSqlQueryModel.data(self,index,role)
            
            ftype = field.get("type", "vchar")
            optionlist = field.get("optionlist",None)
            valuelist = field.get("valuelist",optionlist)
            format = field.get("format",None)
            if not optionlist:
                if ctype == "b":
                    optionlist = [True,False,None]
                    valuelist = [u"Sí",u"No","--"]
            
            if ret.isNull(): ret = None
            if ret is None:
                if ctype == "d": ret = QtCore.QVariant(date.today().isoformat())
                if ctype == "dt": ret = QtCore.QVariant(datetime.now().isoformat())
                if ctype == "b": ret = QtCore.QVariant(False)
                if ctype == "n": ret = QtCore.QVariant(0)
                #if ctype == "s":
                #    if field.get("tableEditable", None)==False:
                #        ret = QtCore.QVariant(random.randrange(1,9999))
            if ret:
                try:
                    if ctype == "b": ret = ret.toBool()
                    if ctype == "d": ret = ret.toDate()
                    if ctype == "dt": ret = ret.toDateTime()
                    if ctype == "s": ret = ret.toString()
                    if ctype == "t": ret = ret.toTime()
                    if ctype == "n": 
                        if ftype == "int": ret, ok = ret.toInt()
                        else: ret, ok = ret.toDouble()                            
                            
                except ValueError: 
                    ret = None
                            
            if role == QtCore.Qt.DisplayRole:
                try:
                    if optionlist:
                        idx = optionlist.index(ret)
                        if idx >= 0: ret = valuelist[idx]
                    elif format:
                        if ctype in ('n','s'):
                            ret = format % ret
                        elif ctype in ('d','dt'):
                            ret = ret.toString(format)
                            
                except Exception, e:
                    pass     
                    
            return ret       
        return QtSql.QSqlQueryModel.data(self,index,role)
        
    def setData(self, index, value, role):
        if value == self.data(index, role): return False
        if role == QtCore.Qt.EditRole:
            row = index.row()
            col = index.column()
            if row not in self.dirtyrows:
                self.dirtyrows[row] = {}
            if col not in self.dirtyrows[row]:
                self.dirtyrows[row][col] = None
            self.dirtyrows[row][col] = QtCore.QVariant(value)
            model = index.model()
            #columns = model.columnCount()
            left = model.index(row,0)
            #right = model.index(row,columns-1)
            
            self.emit(QtCore.SIGNAL("dataChanged(QModelIndex,QModelIndex)"), left,left)
            
            """
            primaryKeyIndex = self.index(index.row(), self.pkidx)
            pkeyval = self.data(primaryKeyIndex)

            self.clear()
            try:
                return self.setValue(pkeyval, self.tmd.field[index.column()]['name'], value)
            finally:
                self.refresh()
            """
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
            
    def commitDirtyRow(self, row):
        if row not in self.dirtyrows: 
            return False 

        result = self.setValues(self.dirtyrows[row])
        if result==True: del self.dirtyrows[row]

    def setValues(self, dirtyrow):
        values = []
        fields = []
        for col, value in dirtyrow.iteritems():
            field = self.tmd.field[col]['name']
            values.append("'"+unicode(value.toString())+"'")
            fields.append(field)            
            
        query = QtSql.QSqlQuery(self.db)
        query.prepare("INSERT INTO %(table)s (%(fields)s) VALUES(%(values)s)" %
                    {
                        'table' : self.table,
                        'fields' : ", ".join(fields),
                        'values' : ", ".join(values),
                    })
        return query.exec_()
        
        
class QSqlMetadataModel(QMetadataModel):
    def __init__(self, parent, db, tmd = None):
        QMetadataModel.__init__(self, parent, db, tmd)
        self.filter = None
        self.sort = None
    
    def rowCount(self, parent = None):
        if parent is None: parent = QtCore.QModelIndex()
        if parent.isValid(): raise ValueError, "Valid parent passed to rowCount"
        return self.query().size ()
        
    def getFilter(self):
        return self.filter
    
    def setFilter(self, filter):
        self.filter = filter + " "
    
    def setBasicFilter(self, alias=None, text=None):
        if text is None or alias is None: self.filter = None
        else:        
            fieldname=""
            for i, fname in enumerate(self.tmd.fieldlist):
                field = self.tmd.field[i]
                if unicode(field['alias']) == unicode(alias) or unicode(fname) == unicode(alias):
                    fieldname = fname
                    break
            
            self.filter = " "+fieldname+"::VARCHAR ILIKE '%"+text+"%' "
    
    def setSort(self, col, desc):
        # sorts column col ascending, or descending if desc == True
        field = self.tmd.fieldlist[col]
        self.sort = "ORDER BY "+field+" "
        if desc==1: self.sort += "DESC"
    
    def commitDirtyRow(self, row):
        if row not in self.dirtyrows: 
            return False 
            
        primaryKeyIndex = self.index(row, self.pkidx)
        pkeyval = self.data(primaryKeyIndex)
        
        self.setValues(pkeyval, self.dirtyrows[row])
        del self.dirtyrows[row]
        self.refresh()

    def setValues(self, pkvalue, dirtyrow):
        values = []
        fields = []
        for col, value in dirtyrow.iteritems():
            field = self.tmd.field[col]['name']
            values.append(value)
            fields.append(" %s = ? " % field)
            
        query = QtSql.QSqlQuery(self.db)
        query.prepare("UPDATE %(table)s SET %(setfields)s WHERE %(pk)s = ?" %
                    {
                        'table' : self.table,
                        'setfields' : ", ".join(fields),
                        'pk' : self.pk,
                    })
        for value in values:
            query.addBindValue(value)
        query.addBindValue(pkvalue)
        return query.exec_()
    
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
        query = "SELECT %s FROM %s " %  (", ".join(self.tmd.fieldlist), self.table)
        if self.filter: query+="WHERE "+self.filter
        if self.sort: query+=self.sort
        else: query+="ORDER BY %s" % (self.pk)
        print query
        self.setQuery(query, self.db)
        if self.lastError().isValid():
            print "Error Query: ", self.lastError();
            
    select = refresh
