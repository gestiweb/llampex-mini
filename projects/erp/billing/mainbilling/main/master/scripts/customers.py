# encoding: UTF-8
print "loading customers.py"
import os.path, traceback
from PyQt4 import QtGui, QtCore, uic
from masterform import LlampexMasterForm


class MasterScript(object):
    def __init__(self, form):
        self.form = form
        print "started init"
        self.form.ui.table.setHorizontalHeaderLabels(["CCode","Customer Name","NIF"])
        