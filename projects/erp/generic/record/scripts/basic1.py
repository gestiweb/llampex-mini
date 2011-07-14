# encoding: UTF-8
from llampexwidgets import LlItemView
from PyQt4 import QtGui, QtCore, uic
import time

class RecordScript(object):
    def __init__(self, project, form):
        self.project = project
        self.form = form
        self.rpc = self.form.prjconn
        
        self.db = self.rpc.qtdb
        self.table = self.form.actionobj.table
        self.ui = form.ui
        self.model = form.model
        self.tmd = form.tmd
        self.row = form.row
                
                
