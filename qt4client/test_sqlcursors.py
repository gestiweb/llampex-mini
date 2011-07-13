# encoding: UTF-8
from PyQt4 import QtCore, QtGui, QtSql
import objects.sqlcursor as cursor
import sys, os, os.path
from login import ConfigSettings, SplashDialog
import bjsonrpc
import qsqlrpcdriver.qtdriver as qtdriver
import time
from datetime import timedelta, datetime
import projectloader
import math

def apppath(): return os.path.abspath(os.path.dirname(sys.argv[0]))
def filepath(): return os.path.abspath(os.path.dirname(__file__))

def appdir(x): # convierte una ruta relativa a la aplicación en absoluta
    if os.path.isabs(x): return x
    else: return os.path.join(apppath(),x)
def filedir(x): # convierte una ruta relativa a este fichero en absoluta
    if os.path.isabs(x): return x
    else: return os.path.join(filepath(),x)


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
        cols = rows
        
        
        self.notificar("Acciones: (%d) " % (actions_sz))
        for i,action in enumerate(sorted(self.project.action_index.keys())):
            col = i % cols
            row = (i - col) / cols
            widget = QtGui.QPushButton(unicode(action), self.tabwidget_p2actions)
            def button_clicked():
                return self.action_clicked(action)
            self.connect(widget, QtCore.SIGNAL("clicked()"), button_clicked)
            self.tab2layout.addWidget(widget, row, col)
            self.notificar(" * %s" % action)
    
        self.notificar("Proyecto cargado.")
        
    def action_clicked(self, action):
        print "clicked", action
        
app = QtGui.QApplication(sys.argv) # Creamos la entidad de "aplicación"

testdialog = TestDialog()
testdialog.show() # el método show asegura que se mostrará en pantalla.


retval = app.exec_() # ejecutamos la aplicación. A partir de aquí perdemos el

sys.exit(retval) # salimos de la aplicación con el valor de retorno adecuado.

