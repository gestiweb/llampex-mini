# encoding: UTF-8
from PyQt4 import QtCore, QtGui, QtSql
from objects.sqlcursor import SqlCursor
import sys, os, os.path
from login import ConfigSettings, SplashDialog
import bjsonrpc
import qsqlrpcdriver.qtdriver as qtdriver
import time
from datetime import timedelta, datetime
import projectloader
import math, itertools
import weakref

def apppath(): return os.path.abspath(os.path.dirname(sys.argv[0]))
def filepath(): return os.path.abspath(os.path.dirname(__file__))

def appdir(x): # convierte una ruta relativa a la aplicación en absoluta
    if os.path.isabs(x): return x
    else: return os.path.join(apppath(),x)
def filedir(x): # convierte una ruta relativa a este fichero en absoluta
    if os.path.isabs(x): return x
    else: return os.path.join(filepath(),x)

def signalFactory(dest, *args):
    def fn():
        return dest(*args)
    return fn

class TestDialog(QtGui.QDialog):
    def __init__(self):
        QtGui.QDialog.__init__(self)
        self.setWindowTitle("Test de Cursores (SqlCursor)")
        self.datetext = None
        self.notificacion = QtGui.QLabel(self)
        self.tabwidget = QtGui.QTabWidget(self)
        self.tabwidget_p1log = QtGui.QWidget(self.tabwidget)
        self.tabwidget_p2actions = QtGui.QWidget(self.tabwidget)
        self.tabwidget.addTab(self.tabwidget_p1log, "Log/Registro")
        self.tabwidget.addTab(self.tabwidget_p2actions, "Actions")
        self.layout = QtGui.QVBoxLayout(self)
        self.layout.addWidget(self.tabwidget)
        self.layout.addWidget(self.notificacion)
        
        
        self.logbox = QtGui.QTextEdit(self.tabwidget)
        self.logbox.setFrameStyle(QtGui.QFrame.StyledPanel | QtGui.QFrame.Plain)
        self.logbox.setReadOnly(True)
        self.logbox.setFocusPolicy(QtCore.Qt.NoFocus)
        self.tab1layout = QtGui.QVBoxLayout(self.tabwidget_p1log)
        #self.layout.addStretch()
        self.tab1layout.addWidget(self.logbox)
        self.tab2layout = QtGui.QGridLayout(self.tabwidget_p2actions)
        QtCore.QTimer.singleShot(50, self.iniciar)
        self.resize(400,300)
        self.notificar("Esperando . . .")
        self.date = None
        self.splash = SplashDialog()
        self.splash.finishLoad = self.fin_carga
        self.dialogs = {}    
    
    def notificar(self, text):
        date = datetime.today()
        datetext = unicode(date.strftime("%A, %d. %B %Y %H:%M"), "UTF8")
        if self.datetext != datetext:
            self.datetext = datetext
            self.logbox.insertHtml(u"<br /><b>%s</b><br />" % datetext)
        htmltext = u"(%s) %s<br />" % (unicode(date.strftime("%S.%f"),"UTF8"),text)            
        self.notificacion.setText(text)
        self.notificacion.repaint()
        self.logbox.insertHtml(htmltext)
        self.forceRedraw()

    def forceRedraw(self):
        evLoop = QtCore.QEventLoop(self)
        evLoop.processEvents( QtCore.QEventLoop.ExcludeUserInputEvents, 50)
        
    def iniciar(self):
        
        self.notificar("Inicializando . . .")
        settings = ConfigSettings.load()
        
        self.conn = bjsonrpc.connect(host=settings.host,port=int(settings.port))
        self.notificar("Conectado.")
        # self.conn._debug_socket = True
        logged = self.conn.call.login(settings.username,settings.password)
        assert(logged)
        self.notificar("Registrado.")
        availableprojects  = self.conn.call.getAvailableProjects()
        project = availableprojects[0]['code']
        self.prj = self.conn.call.connectProject(project)
        self.notificar("Proyecto conectado.")
        self.splash.prjconn = self.prj

        self.prj.qtdriver = qtdriver.QSqlLlampexDriver(self.prj)
        self.prj.qtdb = QtSql.QSqlDatabase.addDatabase(self.prj.qtdriver, "llampex-qsqlrpcdriver")
        if not self.prj.qtdb.open("",""):
            print "ERROR: Error trying to connect Qt to RPC Database."
        self.notificar("Esperando a fin de carga.")
        self.splash.show()

    def fin_carga(self):
        self.notificar("Carga finalizada, cargando proyecto . . . ")
        self.projectpath = self.splash.projectpath
        self.projectfiles = self.splash.rprj.files
        
        self.prjloader = projectloader.ProjectLoader(self.projectpath,self.projectfiles)
        self.project = self.prjloader.load()
        tableindex = projectloader.LlampexTable.tableindex
        actions_sz = len(self.project.action_index.keys())
        rows = int(math.ceil(math.sqrt(float(actions_sz))))
        cols = int(math.ceil(rows / 2.2))
        
        
        self.notificar("Acciones: (%d) " % (actions_sz))
        modules = {}
        for action in self.project.action_index.values():
            module = action.parent.parent
            if module not in modules: modules[module] = []
            modules[module].append(action)
        i = itertools.count()
        def nextval(c):
            i = c.next()
            col = i % cols
            row = (i - col) / cols
            i+=1
            return row,col
        
        for module, actions in sorted(modules.iteritems()):
            row, col = nextval(i)
            while col != 0: row, col = nextval(i)
            widget = QtGui.QLabel("%s module (%s area)" % (module.name, module.parent.name), self.tabwidget_p2actions)
            self.notificar(" **> %s - %s " % (module.code, module.name))
            self.tab2layout.addWidget(widget, row, col)
            while col != cols-1: row, col = nextval(i)
            for action in sorted(actions):
                row, col = nextval(i)
                widget = QtGui.QPushButton(action.name, self.tabwidget_p2actions)
                self.connect(widget, QtCore.SIGNAL("clicked()"), signalFactory(self.action_clicked,widget,action.code))
                self.tab2layout.addWidget(widget, row, col)
                self.notificar(" * %s - %s" % (action.code, action.name))
    
        self.notificar("Proyecto cargado.")
        
    def action_clicked(self, widget, actioncode):
        if actioncode not in self.dialogs:
            dialog = TestSqlCursorDialog(self, self.project, self.prj, actioncode)
            self.dialogs[actioncode] = dialog
        self.dialogs[actioncode].show()

class TestSqlCursorDialog(QtGui.QDialog):
    def tbutton(self, title, action = None):
        button = QtGui.QToolButton(self)
        button.setText(title)
        self.buttonLayout.addWidget(button)
        if action:
            if type(action) is list or type(action) is tuple: 
                self.connect(button, QtCore.SIGNAL("clicked()"), *action)
            else:
                self.connect(button, QtCore.SIGNAL("clicked()"), action)
        return button
        
    def __init__(self, parent, project, rpc, actioncode):
        QtGui.QDialog.__init__(self)
        self.project = project
        self.parent = parent
        self.prjconn = rpc
        self.action = self.project.action_index[actioncode]
        self.table = self.project.table_index[self.action.table]
        
        print "Loading", self.action.name
        self.setWindowTitle("(SqlCursor) %s -> %s" % (self.action.name, self.table.name))
        self.layout = QtGui.QVBoxLayout(self)
        self.title = QtGui.QLabel(self.action.name)
        self.title.setAlignment(QtCore.Qt.AlignCenter)
        font = self.title.font()
        font.setBold(True)
        self.title.setFont(font)
        
        self.table = QtGui.QTableView(self)
        self.table.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
        self.layout.addWidget(self.title)
        self.buttonLayout = QtGui.QHBoxLayout()
        self.tbInsert = self.tbutton("Insert")
        self.tbDelete = self.tbutton("Delete")
        self.tbCommit = self.tbutton("Commit", action=self.buttonCommit_clicked)
        self.tbRevert = self.tbutton("Revert", action=self.buttonRevert_clicked)
        self.buttonLayout.addStretch()
        self.layout.addLayout(self.buttonLayout)
        self.layout.addWidget(self.table)
        self.cursor = SqlCursor(self.project, self.prjconn, self.action.code)
        self.cursor.select()
        self.cursor.configureViewWidget(self.table)
        self.resize(600,400)
        
    def closeEvent(self,event):
        del self.parent.dialogs[self.action.code]
        event.accept()
    
    def buttonCommit_clicked(self):
        self.cursor.commitBuffer()
        
    def buttonRevert_clicked(self):
        self.cursor.refreshBuffer()
    
        
app = QtGui.QApplication(sys.argv) 

testdialog = TestDialog()
testdialog.show()


retval = app.exec_()
sys.exit(retval) # salimos de la aplicación con el valor de retorno adecuado.

