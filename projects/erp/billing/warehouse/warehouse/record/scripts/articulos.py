# encoding: UTF-8
from llampexwidgets import LlItemView
from llitemview import LlItemView1
from PyQt4 import QtGui, QtCore, uic

def _getAllWidgets(form):
    widgets = []
    for obj in form.children():
        if isinstance(obj, QtGui.QWidget):
            widgets.append(obj)
            widgets+=_getAllWidgets(obj)
    return widgets

def getAllWidgets(form):
    return [ obj for obj in _getAllWidgets(form) if obj.objectName() ]

class RecordScript(object):
    def __init__(self, form):
        self.form = form
        self.rpc = self.form.prjconn
        
        self.db = self.rpc.qtdb
        self.table = self.form.actionobj.table
        self.ui = form.ui
        self.model = form.model
        self.tmd = form.tmd
        self.row = form.row
        
        for obj in getAllWidgets(self.ui):
            if isinstance(obj, LlItemView):
                column = self.tmd.fieldlist.index(obj.fieldName)
                print obj.objectName(), obj.fieldName, column
                if column >= 0:
                    widget = LlItemView1(obj)
                    widget.setup()
                    widget.setModel(self.model)
                    widget.setCol(column)
                    widget.setRow(self.row)
                    obj.replaceEditorWidget(widget)
                    
                
                
