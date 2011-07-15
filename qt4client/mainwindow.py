# encoding: UTF-8
import os.path, traceback
import yaml

from PyQt4 import QtGui, QtCore, uic

from widgets import llampexmainmenu, llampexgroupbutton

from masterform import LlampexMasterForm

import projectloader


__version__ = "0.0.1"

def filepath(): return os.path.abspath(os.path.dirname(__file__))
def filedir(x): # convierte una ruta relativa a este fichero en absoluta
    if os.path.isabs(x): return x
    else: return os.path.join(filepath(),x)

class LlampexMdiSubWindow(QtGui.QMdiSubWindow):
    windowdict = {}
    def __init__(self, windowkey, widget):
        QtGui.QMdiSubWindow.__init__(self)
        self.windowkey = windowkey
        if self.windowkey in self.windowdict:
            print "!Window %s already opened, closing prior to creating it again." % self.windowkey
            self.windowdict[self.windowkey].close()
            
        self.windowdict[self.windowkey] = self
        self.setWidget(widget)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.widget = widget
    
    @classmethod
    def close_window(cls,key):
        if key in cls.windowdict:
            self = cls.windowdict[key]
            self.close()
    
    def closeEvent(self,event):
        #print "Closing", self.windowkey
        try:
            if self.windowkey in self.windowdict:
                del self.windowdict[self.windowkey]
        finally:
            event.accept()
            
            
class LlampexSearchBox(QtGui.QLineEdit):
    
    def __init__(self, parent):
        QtGui.QLineEdit.__init__(self)
        
        self.clearButton = QtGui.QToolButton(self)
        pixmap = QtGui.QPixmap("icons/searchClear.png")
        self.clearButton.setIcon(QtGui.QIcon(pixmap))
        self.clearButton.setIconSize(pixmap.size())
        self.clearButton.setCursor(QtCore.Qt.ArrowCursor)
        self.clearButton.setStyleSheet("QToolButton { border: none; padding: 0px; }")
        self.clearButton.hide()
        self.connect(self.clearButton, QtCore.SIGNAL("clicked()"), self.clearClicked)
        self.connect(self,QtCore.SIGNAL("textChanged(const QString&)"), self.updateClearButton)
        self.frameWidth = self.style().pixelMetric(QtGui.QStyle.PM_DefaultFrameWidth)
        self.setStyleSheet(QtCore.QString("QLineEdit { padding-right: %1px; color: gray; } ").arg(self.clearButton.sizeHint().width()+self.frameWidth+1))
        self.setText("Search...")
        msz = self.minimumSizeHint()
        self.setMinimumSize(self.qMax(msz.width(), self.clearButton.sizeHint().height() + self.frameWidth * 2 + 2),
                            self.qMax(msz.height(), self.clearButton.sizeHint().height() + self.frameWidth * 2 + 2))
    
    def qMax(self, a1,  a2):
        if a1 <= a2:
            return a2
        else:
            return a1
    
    def clearClicked(self):
        self.clear()
    
    def resizeEvent(self, event):
        sz = self.clearButton.sizeHint()
        self.frameWidth = self.style().pixelMetric(QtGui.QStyle.PM_DefaultFrameWidth)
        self.clearButton.move(self.rect().right() - self.frameWidth - sz.width(), (self.rect().bottom() + 1 - sz.height())/2)
    
    def focusInEvent(self, event):
        QtGui.QLineEdit.focusInEvent(self, event)
        if (self.text() == "Search..."):
            self.setStyleSheet(QtCore.QString("QLineEdit { padding-right: %1px; color: black } ").arg(self.clearButton.sizeHint().width()+self.frameWidth+1))
            self.setText("")
            
    def focusOutEvent(self,event):
        QtGui.QLineEdit.focusOutEvent(self, event)
        if (self.text().isEmpty()):
            self.setStyleSheet(QtCore.QString("QLineEdit { padding-right: %1px; color: gray } ").arg(self.clearButton.sizeHint().width()+self.frameWidth+1))
            self.setText("Search...")
        
    def updateClearButton(self, text):
        if (text.isEmpty() or text == "Search..."):
            self.clearButton.setVisible(False) 
        else:
            self.clearButton.setVisible(True)
  

class LlampexMainWindow(QtGui.QMainWindow):
    def prjdir(self, x):
        return os.path.join(self.projectpath,x)
        
    def __init__(self, projectpath, projectfiles, prjconn):
        QtGui.QMainWindow.__init__(self)
        self.prjconn = prjconn # rpc connection for project.
        self.mainmenu = llampexmainmenu.LlampexDockMainMenu()
        self.setWindowTitle("Llampex Qt4 Client")
        self.projectpath = projectpath
        self.projectfiles = projectfiles

        self.searchIcon = QtGui.QIcon("icons/search.png")

        try:
            self.prjloader = projectloader.ProjectLoader(projectpath,projectfiles)
            self.project = self.prjloader.load()
            self.load()
        except Exception:
            print traceback.format_exc()
            print "Some error ocurred when loading your project. Loading default demo."
            self.load_demo()
    
    def load(self):
        self.modules = {}
        self.actions = {}
        for area_code in self.project.area_list:
            areaobj = self.project.area[area_code]
            icon = None
            item = self.mainmenu.addItem(unicode(areaobj.name))
            item.setDefaultCallback(self.menubutton_clicked)
            if areaobj.icon:
                iconfile = areaobj.filedir(areaobj.icon)
                icon = QtGui.QIcon(iconfile)
                item.button.setIcon(icon)
            if areaobj.description:
                item.button.setDescription(areaobj.description)
                item.button.setMaximumHeight(64)
            else:
                item.button.setMaximumHeight(32)
                
            for module_code in areaobj.module_list:
                moduleobj = areaobj.module[module_code]
                module_key = "%s.%s" % (areaobj.code,moduleobj.code)
                subitem = item.addItem(unicode(moduleobj.name),module_key)
                icon = None
                if moduleobj.icon:
                    iconfile = moduleobj.filedir(moduleobj.icon)
                    icon = QtGui.QIcon(iconfile)
                    subitem.setIcon(icon)
                self.modules[module_key] = (icon, moduleobj)
        self.modulesubwindow = {}
                    
        self.finish_load()        
    
    def finish_load(self):
        self.addDockWidget(QtCore.Qt.LeftDockWidgetArea,self.mainmenu)

        toolbar = self.addToolBar("Llampex Toolbar")
        toolbar.setMovable(False)
        self.searchBox = LlampexSearchBox(toolbar)
        self.connect(self.searchBox, QtCore.SIGNAL("returnPressed()"), self.searchPerformed)

        mainframe = QtGui.QFrame(self)
        mainframe.setLayout(QtGui.QVBoxLayout(mainframe))
        
        toolframe = QtGui.QFrame(self)
        toolframe.setLayout(QtGui.QHBoxLayout(toolframe))
        toolframe.layout().addWidget(self.searchBox,0,QtCore.Qt.AlignRight)
        
        mainframe.layout().addWidget(toolframe)
        
        self.mdiarea = QtGui.QMdiArea()
        self.mdiarea.setBackground(QtGui.QBrush())
        self.mdiarea.setViewMode(QtGui.QMdiArea.TabbedView)
        self.mdiarea.setDocumentMode(True)
        #self.setCentralWidget(self.mdiarea)
        mainframe.layout().addWidget(self.mdiarea)
        self.setCentralWidget(mainframe)
        
    def searchPerformed(self):
        if (not self.searchBox.text().isEmpty()):
            search = unicode(self.searchBox.text()).lower()
            searchText = [u"Searching '%s':\n" % search]
            widget = QtGui.QLabel("")
            found = []
            for code, action in self.project.action_index.iteritems():
                aname = unicode(action).lower()
                if aname.find(search):
                    found+=action
                
            for action in sorted(found):
                searchText.append(u" * %s -> %s -> %s" % (action.parent.name, action.parent.name, action.name))
                
            widget.setText("\n".join(searchText))
            widget.setMargin(20)
            
            scrollarea = QtGui.QScrollArea()
            scrollarea.setWidget(widget)
            scrollarea.setWidgetResizable(True)
            scrollarea.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
            scrollarea.setMinimumWidth(250)
            
            subwindow = LlampexMdiSubWindow("Search:"+self.searchBox.text(),scrollarea)
            self.mdiarea.addSubWindow(subwindow)
            
            subwindow.setWindowTitle("Search")
            subwindow.setWindowIcon(self.searchIcon)
            subwindow.show()
            self.mdiarea.setActiveSubWindow(subwindow)
            subwindow.setWindowState(QtCore.Qt.WindowMaximized)
        
            
    def menubutton_clicked(self,key):
        #print "menubutton clicked:", key      
        LlampexMdiSubWindow.close_window(key)  
        """
        if key in self.modulesubwindow:
            subwindow = self.modulesubwindow[key]
            subwindow.close()
            del self.modulesubwindow[key]
        """
        widget = QtGui.QWidget()
        widget.layout = QtGui.QVBoxLayout()
        
        scrollarea = QtGui.QScrollArea()
        scrollarea.setWidget(widget)
        scrollarea.setWidgetResizable(True)
        scrollarea.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        scrollarea.setMinimumWidth(250)
        subwindow = LlampexMdiSubWindow(key,scrollarea)
        self.mdiarea.addSubWindow(subwindow)
        
        moduleicon, moduleobj = self.modules[key] 
        self.modulesubwindow[key] = subwindow

        for group_code in moduleobj.group_list:
            groupboxobj = moduleobj.group[group_code]
            groupbox = llampexgroupbutton.LlampexGroupButton(groupboxobj.name)
            oldweight = None
            for action_code in groupboxobj.action_list:
                actionobj = groupboxobj.action[action_code]
                icon = None
                if actionobj.icon:
                    iconfile = actionobj.filedir(actionobj.icon)
                    icon = QtGui.QIcon(iconfile)
                try:
                    if oldweight and actionobj.weight[0] != oldweight[0]:
                        groupbox.addSeparator()
                except:
                    print repr(actionobj.weight)
                    print repr(oldweight)
                    raise
                action_key = "%s.%s" % (key,action_code)
                self.actions[action_key] = (key,icon, actionobj)
                groupbox.addAction(actionobj.name, action_key, icon, self.actionbutton_clicked)
                oldweight = actionobj.weight

            groupbox.addSeparator(0)
            widget.layout.addWidget(groupbox)
        
        widget.setLayout(widget.layout)
        
        subwindow.show()
        subwindow.setWindowTitle(moduleobj.name)
        subwindow.setWindowIcon(moduleicon)
        self.mdiarea.setActiveSubWindow(subwindow)
        subwindow.setWindowState(QtCore.Qt.WindowMaximized)
    
    def actionbutton_clicked(self, key):
        print "action clicked", key
        subwindowkey, icon, actionobj = self.actions[key]
        if subwindowkey in self.modulesubwindow:
            subwindow = self.modulesubwindow[subwindowkey]
            subwindow.close()
            del self.modulesubwindow[subwindowkey]
         
        
        widget = LlampexMasterForm(self.project, key, actionobj, self.prjconn)
        
        scrollarea = QtGui.QScrollArea()
        scrollarea.setWidget(widget)
        scrollarea.setWidgetResizable(True)
        scrollarea.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        scrollarea.setMinimumWidth(250)
        
        subwindow = LlampexMdiSubWindow(key,scrollarea)
        self.mdiarea.addSubWindow(subwindow)
        
        subwindow.setWindowTitle(actionobj.name)
        subwindow.setWindowIcon(icon)
        subwindow.show()
        self.mdiarea.setActiveSubWindow(subwindow)
        subwindow.setWindowState(QtCore.Qt.WindowMaximized)
        
    
    def load_demo(self):
        self.menubutton_clicked = self.menubutton_clicked_demo
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
        
        self.finish_load()
        

    def menubutton_clicked_demo(self,key):
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
        