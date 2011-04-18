# encoding: UTF-8
import os.path
import yaml

from PyQt4 import QtGui, QtCore, uic

from widgets import llampexmainmenu, llampexgroupbutton



__version__ = "0.0.1"

def filepath(): return os.path.abspath(os.path.dirname(__file__))
def filedir(x): # convierte una ruta relativa a este fichero en absoluta
    if os.path.isabs(x): return x
    else: return os.path.join(filepath(),x)

        

class LlampexMainWindow(QtGui.QMainWindow):
    def prjdir(self, x):
        return os.path.join(self.projectpath,x)
        
    def __init__(self, projectpath):
        QtGui.QMainWindow.__init__(self)
        self.mainmenu = llampexmainmenu.LlampexDockMainMenu()
        self.setWindowTitle("Llampex Qt4 Client")
        self.projectpath = projectpath
        icon_fact = QtGui.QIcon(self.prjdir("facturacion/facturacion/flfacturac.xpm"))
        icon_cont = QtGui.QIcon(self.prjdir("contabilidad/principal/flcontppal.xpm"))
        icon_fppl = QtGui.QIcon(self.prjdir("facturacion/principal/flfactppal.xpm"))
        
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
        iconlist = [
            'forms/accessories-dictionary.png',
            'forms/accessories-text-editor.png',
            'forms/acroread.png',
            'forms/akonadi.png',
            'forms/akregator.png',
            'forms/alevt.png',
            'forms/application-sxw.png',
            'forms/settings.png'
            ]
        icon = []
        for i in iconlist:
            icon.append(QtGui.QIcon(filedir(i)))

        widget = QtGui.QWidget()
        widget.layout = QtGui.QVBoxLayout()
        
        groupbox = llampexgroupbutton.LlampexGroupButton("Principal")
        groupbox.addAction("Empresa", "empresa", icon[0])
        groupbox.addSeparator()
        groupbox.addAction("Clientes", "clientes", icon[1])
        groupbox.addAction("Proveedores", "proveedores", icon[2])
        groupbox.addSeparator(0)
        widget.layout.addWidget(groupbox)
        
        groupbox = llampexgroupbutton.LlampexGroupButton("Fiscalidad")
        groupbox.addAction("Ejercicios\nFiscales", "ejercicios", icon[3])
        groupbox.addAction("Series de\nFacturacion", "series", icon[4])
        groupbox.addAction("Impuestos", "impuestos", icon[5])
        groupbox.addSeparator(0)
        widget.layout.addWidget(groupbox)
        
        groupbox = llampexgroupbutton.LlampexGroupButton("Tablas Generales")
        groupbox.addAction("Cuentas Bancarias", "cuentasbco", icon[6])
        groupbox.addAction("Bancos", "bancos", icon[3])
        groupbox.addSeparator()
        groupbox.addAction("Descuentos", "dtoclientes", icon[7])
        groupbox.addAction("Tipos\nde Pago", "tipospago", icon[0])
        groupbox.addAction("Formas\nde Pago", "formaspago", icon[1])
        groupbox.addAction("Tipos\nde Rappel", "tiposrappel", icon[2])
        groupbox.addSeparator()
        groupbox.addAction("Agentes", "", icon[3])
        groupbox.addAction("Departamentos", "", icon[3])
        groupbox.addAction("Usuarios", "", icon[3])
        groupbox.addSeparator()
        groupbox.addAction("Agencias\nTransporte", "", icon[3])
        groupbox.addSeparator(0)
        widget.layout.addWidget(groupbox)
        
        widget.setLayout(widget.layout)
        scrollarea = QtGui.QScrollArea()
        scrollarea.setWidget(widget)
        scrollarea.setWidgetResizable(True)
        scrollarea.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        scrollarea.setMinimumWidth(250)
        
        subwindow = self.mdiarea.addSubWindow(scrollarea)
        subwindow.show()
        subwindow.setWindowTitle(key)
