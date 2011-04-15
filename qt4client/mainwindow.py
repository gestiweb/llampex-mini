# encoding: UTF-8
import os.path
import yaml

from PyQt4 import QtGui, QtCore, uic

from widgets import llampexmainmenu 


__version__ = "0.0.1"

def filepath(): return os.path.abspath(os.path.dirname(__file__))
def filedir(x): # convierte una ruta relativa a este fichero en absoluta
    if os.path.isabs(x): return x
    else: return os.path.join(filepath(),x)

        

class LlampexMainWindow(QtGui.QMainWindow):
    def __init__(self):
        QtGui.QMainWindow.__init__(self)
        self.mainmenu = llampexmainmenu.LlampexDockMainMenu()
        self.setWindowTitle("Llampex Qt4 Client")
        icon_fact = QtGui.QIcon(filedir(".cache/files/facturacion/facturacion/flfacturac.xpm"))
        icon_cont = QtGui.QIcon(filedir(".cache/files/contabilidad/principal/flcontppal.xpm"))
        icon_fppl = QtGui.QIcon(filedir(".cache/files/facturacion/principal/flfactppal.xpm"))
        
        item_favr = self.mainmenu.addItem(u"Favoritos")
        item_favr.setDefaultCallback(self.menubutton_clicked)
        item_favr.button.setIcon(icon_fppl)
        item_favr.button.setDescription(u"Acciones guardadas")
        item_favr.button.setMaximumHeight(50)
        item_favr.addItem(u"Artículos").setIcon(icon_fppl)
        item_favr.addItem(u"Clientes")
        item_favr.addItem(u"Proveedores")
        item_favr.addItem(u"Fact. clientes").setIcon(icon_fact)
        item_favr.addItem(u"Fact. proveedores").setIcon(icon_fact)
        item_favr.addItem(u"Ventas artículo")
        
        item_fact = self.mainmenu.addItem(u"Facturación")
        item_fact.setDefaultCallback(self.menubutton_clicked)
        item_fact.button.setDescription(u"Artículos, Clientes, Fra...")
        item_fact.button.setIcon(icon_fact)
        item_fact.button.setMaximumHeight(50)
        item_fact.addItem(u"Almacén")
        item_fact.addItem(u"Informes")
        item_fact.addItem(u"Principal").setIcon(icon_fppl)
        item_fact.addItem(u"Tesorería")
        item_fact.addItem(u"Facturación").setIcon(icon_fact)
        item_cont = self.mainmenu.addItem(u"Contabilidad")
        item_cont.setDefaultCallback(self.menubutton_clicked)
        item_cont.button.setDescription(u"Asientos, Amortizaciones..")
        item_cont.button.setMaximumHeight(50)
        item_cont.button.setIcon(icon_cont)
        item_cont.addItem(u"Informes")
        item_cont.addItem(u"Principal").setIcon(icon_cont)
        item_cont.addItem(u"Modelos")
        item_sist = self.mainmenu.addItem(u"Sistema")
        item_sist.setDefaultCallback(self.menubutton_clicked)
        item_sist.button.setDescription(u"Configuración, otros..")
        item_sist.button.setMaximumHeight(50)
        item_sist.addItem(u"Configuración")
        item_sist.addItem(u"Datos")
        item_sist.addItem(u"Exportación")
        self.addDockWidget(QtCore.Qt.LeftDockWidgetArea,self.mainmenu)
        self.mdiarea = QtGui.QMdiArea()
        self.mdiarea.setBackground(QtGui.QBrush())
        self.mdiarea.setViewMode(QtGui.QMdiArea.TabbedView)
        self.mdiarea.setDocumentMode(True)
        self.setCentralWidget(self.mdiarea)
    
    def menubutton_clicked(self,key):
        # print "menubutton clicked:", key
        widget = QtGui.QWidget()
        widget.layout = QtGui.QVBoxLayout()
        groupbox1 = QtGui.QGroupBox(key + " - Group Options 1")
        groupbox2 = QtGui.QGroupBox(key + " - Group Options 2")
        groupbox3 = QtGui.QGroupBox(key + " - Group Options 3")
        widget.layout.addWidget(groupbox1)
        widget.layout.addWidget(groupbox2)
        widget.layout.addWidget(groupbox3)
        widget.setLayout(widget.layout)
        
        subwindow = self.mdiarea.addSubWindow(widget)
        subwindow.show()
        subwindow.setWindowTitle(key)
