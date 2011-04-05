#!/usr/bin/env python
# encoding: UTF-8
import bjsonrpc
from bjsonrpc.exceptions import ServerError
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

class ConnectionDialog(QtGui.QDialog):
    def __init__(self):
        QtGui.QDialog.__init__(self)
            
        ui_filepath = filedir("forms/login.ui") # convertimos la ruta a absoluta
        self.ui = uic.loadUi(ui_filepath,self) # Cargamos un fichero UI externo    
        availableprojects  = c.call.getAvailableProjects()
        for row,rowdict in enumerate(availableprojects):
            listitem = QtGui.QListWidgetItem("%(description)s (%(code)s)" % rowdict)
            listitem.project = rowdict
            self.ui.project.addItem(listitem)
        self.ui.project.setCurrentRow(0)
            
    
    def accept(self):
        project = unicode(self.ui.project.currentItem().project['code'])
        username = unicode(self.ui.user.text())
        password = unicode(self.ui.password.text())
        print "Connect!", username, project
        try:
            logininfo = c.call.login(project,username,password)
            msgBox = QtGui.QMessageBox()
            msgBox.setText("Login successful!")
            msgBox.setIcon(QtGui.QMessageBox.Information)
            msgBox.exec_()
            
        except ServerError, e:
            msgBox = QtGui.QMessageBox()
            if e.args[0] == "DatabaseConnectionError":
                msgBox.setText("The server could not connect to the underlying database")
                msgBox.setIcon(QtGui.QMessageBox.Critical)
            elif e.args[0] == "LoginInvalidError":
                msgBox.setText("The username/password specified is invalid. Try again.")
                msgBox.setIcon(QtGui.QMessageBox.Information)
            else:
                msgBox.setText("The server returned the following error:\n" + repr(e.args[0]))
                msgBox.setIcon(QtGui.QMessageBox.Warning)
                
            msgBox.exec_()
        except Exception, e:
            msgBox = QtGui.QMessageBox()
            msgBox.setText("Unexpected error: %s\n" % e.__class__.__name__ + repr(e.args[0]))
            msgBox.setIcon(QtGui.QMessageBox.Critical)
            msgBox.exec_()
        
    
app = QtGui.QApplication(sys.argv) # Creamos la entidad de "aplicación"
app.setStyleSheet(open(filedir("style.css")).read())

connwindow = ConnectionDialog()
connwindow.show() # el método show asegura que se mostrará en pantalla.

retval = app.exec_() # ejecutamos la aplicación. A partir de aquí perdemos el

sys.exit(retval) # salimos de la aplicación con el valor de retorno adecuado.

