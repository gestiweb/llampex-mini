#!/usr/bin/env python
# encoding: UTF-8
import bjsonrpc
c = bjsonrpc.connect()

import os.path

import sys
from PyQt4 import QtGui, QtCore, uic

def apppath(): return os.path.abspath(os.path.dirname(sys.argv[0]))
def filepath(): return os.path.abspath(os.path.dirname(__file__))

print filepath()

def appdir(x): # convierte una ruta relativa a la aplicación en absoluta
    if os.path.isabs(x): return x
    else: return os.path.join(apppath(),x)
def filedir(x): # convierte una ruta relativa a este fichero en absoluta
    if os.path.isabs(x): return x
    else: return os.path.join(filepath(),x)
    
app = QtGui.QApplication(sys.argv) # Creamos la entidad de "aplicación"

ui_filepath = filedir("forms/login.ui") # convertimos la ruta a absoluta
print "Loading UI FILE: '%s' . . . " % ui_filepath
window = uic.loadUi(ui_filepath) # Cargamos un fichero UI externo

availableprojects  = c.call.getAvailableProjects()
window.tableWidget.setRowCount(len(availableprojects))
row = 0
for code,description in availableprojects:
    item_code = QtGui.QTableWidgetItem(code)
    item_description = QtGui.QTableWidgetItem(description)
    window.tableWidget.setItem(row,0,item_code)
    window.tableWidget.setItem(row,1,item_description)
    row += 1
# y nos devuelve el objeto listo para usar.
print "done."

window.show() # el método show asegura que se mostrará en pantalla.

retval = app.exec_() # ejecutamos la aplicación. A partir de aquí perdemos el

sys.exit(retval) # salimos de la aplicación con el valor de retorno adecuado.

