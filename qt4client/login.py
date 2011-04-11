#!/usr/bin/env python
# encoding: UTF-8
import bjsonrpc
from bjsonrpc.exceptions import ServerError
c = bjsonrpc.connect()

import os.path
import time, threading, traceback

import sys
from PyQt4 import QtGui, QtCore, uic

from base64 import b64decode, b64encode
import yaml, hashlib, bz2, zlib
from widgets import llampexmainmenu

class ConfigSettings(yaml.YAMLObject):
    yaml_tag = u'!ConfigSettings' 

__version__ = "0.0.1"
diskwrite_lock = threading.Lock()

def apppath(): return os.path.abspath(os.path.dirname(sys.argv[0]))
def filepath(): return os.path.abspath(os.path.dirname(__file__))

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
        try:
            f1 = open(filedir(".settings.yaml"),"r")
            settings = yaml.load(f1.read())
        except IOError:
            settings = ConfigSettings()
            settings.username = ""
            settings.password = ""
            settings.remember = False
            settings.project = ""
            
        self.ui.user.setText(settings.username)
        self.ui.password.setText(settings.password)
        self.ui.rememberpasswd.setChecked(settings.remember)

        selected = 0
        availableprojects  = c.call.getAvailableProjects()
        for row,rowdict in enumerate(availableprojects):
            listitem = QtGui.QListWidgetItem("%(description)s (%(code)s)" % rowdict)
            listitem.project = rowdict
            if rowdict['code'] == settings.project: selected = row
            self.ui.project.addItem(listitem)
        self.ui.project.setCurrentRow(selected)
            
    
    def accept(self):
        project = unicode(self.ui.project.currentItem().project['code'])
        username = unicode(self.ui.user.text())
        password = unicode(self.ui.password.text())
        
        try:
            project_manager = c.call.login(project,username,password)
            if not project_manager: raise ValueError
            #msgBox = QtGui.QMessageBox()
            #msgBox.setText("Login successful!")
            #msgBox.setIcon(QtGui.QMessageBox.Information)
            #msgBox.exec_()
            # print project_manager.call.getUserList()
            #filelist = project_manager.call.getFileList()
            #print sorted( filelist.keys() )
            splashwindow = SplashDialog()
            splashwindow.prjconn = project_manager
            splashwindow.show()
            self.close()
            
            
            
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

    def reject(self):
        self.close()
    

    
    def closeEvent(self,event):
        settings = ConfigSettings()
        if self.ui.rememberpasswd.isChecked():
            settings.project = str(self.ui.project.currentItem().project['code'])
            settings.username = str(self.ui.user.text())
            settings.password = str(self.ui.password.text())
            settings.remember = True
        else:
            settings.project = ""
            settings.username = ""
            settings.password = ""
            settings.remember = False
        f1 = open(filedir(".settings.yaml"),"w")
        f1.write(yaml.dump(settings))
        event.accept()
        #event.ignore()
        
class remoteProject(object):
    pass

def trb64_name(b64): #translate b64 to filename
    filename = "cache_" + b64.replace("+","_") + ".data"
    filename = filename.replace("/","-")
    return filename

class SplashDialog(QtGui.QDialog):
    def __init__(self):
        QtGui.QDialog.__init__(self)
        self.prjconn = None
        ui_filepath = filedir("forms/splash.ui") # convertimos la ruta a absoluta
        self.ui = uic.loadUi(ui_filepath,self) # Cargamos un fichero UI externo    
        self.ui.version.setText("v%s" % __version__)
        self.ui.progress.setValue(0)
        wf = self.windowFlags()
        self.setWindowFlags(wf | QtCore.Qt.FramelessWindowHint)
        self.rprj = remoteProject()
        self.progress_value = 0
        self.prev_load_mode = None
        self.load_mode = "init"
        self.progress_load = {
            "init" : 10,
            "waitload" : 100,
            "filetree" : 110,
            "projectsignature" : 120,
            "projectparts1" : 130,
            "projectdownload" : 300,
            "end" : 1000,
            "error" : 0,
        }
        self.status_load = {
            "init" : "Initializing ...",
            "waitload" : "Waiting until server is ready ...",
            "filetree" : "Obtaining project tree from server ...",
            "projectsignature" : "Querying project signature ...",
            "projectparts1" : "Querying project contents ...",
            "projectdownload" : "Downloading project files ...",
            "end" : "Load finished.",
            "error" : "Unexpected error ocurred!!",
        }
        self.speed_load = {
            "init" : 1,
            "waitload" : 0.2,
            "filetree" : 1,
            "projectsignature" : 1,
            "projectparts1" : 1,
            "projectdownload" : 0.5,
            "end" : 25,
            "error" : 1,
        }
        self.waiting = 0
        self.timer = QtCore.QTimer(self)
        self.connect(self.timer, QtCore.SIGNAL("timeout()"), self.timer_timeout)
        self.timer.start(20)
        self.status_extra = ""
        self.progress_extra = 0
        
        self.statusthread = threading.Thread(target=self.updateLoadStatus)
        self.statusthread.daemon = True
        self.statusthread.start()
        
    def timer_timeout(self):       
        self.progress_value = (self.progress_value * 100.0 + (self.progress_extra + self.progress_load[self.load_mode]) * self.speed_load[self.load_mode]) / (self.speed_load[self.load_mode]+100.0)
        
        self.ui.progress.setValue(int(self.progress_value))
        status = self.status_load[self.load_mode]
        if self.status_extra:
            status += " (%s)" % self.status_extra
        self.ui.status.setText( status )
        if self.prev_load_mode != self.load_mode:
            self.changedMode(self.prev_load_mode, self.load_mode)
            self.prev_load_mode = self.load_mode
        if self.progress_value > 999: self.close()
    
    def changedMode(self,frommode,tomode):
        #print frommode, tomode
        try:
            if tomode == "end": self.finishLoad()
        except:
            print traceback.format_exc()
        
    
    
    def updateLoadStatus(self):
        try:
            time.sleep(0.05)
            self.load_mode = "init"
            while self.prjconn is None: 
                time.sleep(0.05)
            
            time.sleep(0.05)
            self.load_mode = "waitload"
            while not self.prjconn.call.isLoaded():
                time.sleep(0.5)
        
            time.sleep(0.05)
            self.load_mode = "filetree"
            self.rprj.filetree = self.prjconn.call.getFileTree()
        
            time.sleep(0.05)
            self.load_mode = "projectsignature"
            key, size, signature = self.rprj.filetree.call.getNodeSignature()
            self.rprj.project_signature = signature
            self.rprj.project_size = size
        
            time.sleep(0.05)
            self.load_mode = "projectparts1"
            self.rprj.project_childs = self.rprj.filetree.call.getChildSignature()
            self.rprj.files = {}
            sz = len(self.rprj.project_childs)
            for i,k in enumerate(self.rprj.project_childs):
                p = i*100/sz
                self.status_extra = "%d%%" % (p)
                self.progress_extra = p
                nodevalues = self.rprj.filetree.call.getNodeHashValue([k])
                for nodehash, nodeval in nodevalues.iteritems():
                    digest = nodeval['digest']
                    name = nodeval['name']
                    self.rprj.files[name] = digest
        
            p = 100
            self.status_extra = "%d%%" % (p)
            self.progress_extra = 100
        
            time.sleep(0.05)
            self.status_extra = ""
            self.progress_extra = 0
            self.load_mode = "projectdownload"
            cachedir = filedir(".cache/files")
            try:
                os.makedirs(cachedir)
            except os.error:
                pass
            sz = len(self.rprj.files)
            th1_queue = []
            delta = [0,0,0,0]
            for i,name in enumerate(self.rprj.files):
                p = i*100/sz
                self.progress_extra = p
                
                def download(name,result):
                    t1 = time.time()
                    fullfilename = os.path.join(cachedir,name)
                    cachefilename = os.path.join(cachedir,trb64_name(self.rprj.files[name]))
                    
                    folder = os.path.dirname(fullfilename)
                    try:
                        os.makedirs(folder)
                    except os.error:
                        pass
                    
                    basename = os.path.basename(name)
                    t2 = time.time()
                    value = self.prjconn.call.getFileName(name)
                    t3 = time.time()
                    f_contents = bz2.decompress(b64decode(value))
                    del value
                    t4 = time.time()
                    f1 = open(fullfilename,"w")
                    f1.write(f_contents)
                    f1.close()
                    
                    t5 = time.time()
                    self.status_extra = "%d%% %s" % (p,basename)
                    delta[0] += t2-t1
                    delta[1] += t3-t2
                    delta[2] += t4-t3
                    delta[3] += t5-t4
                    #newdigest = get_b64digest(f_contents)
                    #try:
                    #    assert(newdigest == self.rprj.files[name])
                    #except AssertionError:
                    #    print "PANIC: Digest assertion error for", name
                        
                while len(th1_queue) > 64:
                    if th1_queue[0].is_alive():
                        th1_queue[0].join(3)
                        
                    if th1_queue[0].is_alive():
                        print "Stuck:", th1_queue[0].filename
                    del th1_queue[0]
                #download(name)
                fullfilename = os.path.join(cachedir,name)
                sha1_64 = None
                
                f1 = None
                try:
                    f1 = open(fullfilename)
                    sha1_64 = get_b64digest(f1.read())
                    f1.close()
                except IOError:
                    sha1_64 = ""
                
                if sha1_64 != self.rprj.files[name]:
                    th1 = threading.Thread(target=download,kwargs={'name':name,'result':None})
                    th1.filename = name
                    th1.start()
                    th1_queue.append(th1)
                
            self.status_extra = "syncing"
            while len(th1_queue) > 0:
                if th1_queue[0].is_alive():
                    th1_queue[0].join(3)
                self.status_extra = "syncing"
                    
                if th1_queue[0].is_alive():
                    print "Stuck:", th1_queue[0].filename
                del th1_queue[0]
            
            if delta != [0,0,0,0]:
                print "Time Deltas:", delta
            self.progress_extra = 0
            self.status_extra = ""
            self.load_mode = "end"
            
            
        except:        
            self.load_mode = "error"
            raise
            
    def finishLoad(self): 
        global mainwin
        mainwin = LlampexMainWindow()
        mainwin.show()
        

        

class LlampexMainWindow(QtGui.QMainWindow):
    def __init__(self):
        QtGui.QMainWindow.__init__(self)
        self.mainmenu = llampexmainmenu.LlampexDockMainMenu()
        item_fact = self.mainmenu.addItem(u"Facturación")
        item_fact.addItem(u"Almacén")
        item_fact.addItem(u"Informes")
        item_fact.addItem(u"Principal")
        item_fact.addItem(u"Tesorería")
        item_cont = self.mainmenu.addItem(u"Contabilidad")
        item_cont.addItem(u"Informes")
        item_cont.addItem(u"Principal")
        item_sist = self.mainmenu.addItem(u"Sistema")
        item_sist.addItem(u"Configuración")
        self.addDockWidget(QtCore.Qt.LeftDockWidgetArea,self.mainmenu)
        self.mdiarea = QtGui.QMdiArea()
        self.mdiarea.setBackground(QtGui.QBrush())
        self.setCentralWidget(self.mdiarea)

    
def get_b64digest(text):
    bindigest = hashlib.sha1(text).digest()
    b64digest = b64encode(bindigest)[:20]
    return b64digest

    
try:        
    import formimages
except ImportError:
    print "formimages.py not found. Probably you forgot to do 'pyrcc forms/..qrc -i formimages.py'"

app = QtGui.QApplication(sys.argv) # Creamos la entidad de "aplicación"

# Iniciar como: python login.py -stylesheet styles/llampex1/style.css
# app.setStyleSheet(open(filedir("styles/llampex1/style.css")).read())

connwindow = ConnectionDialog()
connwindow.show() # el método show asegura que se mostrará en pantalla.

retval = app.exec_() # ejecutamos la aplicación. A partir de aquí perdemos el

sys.exit(retval) # salimos de la aplicación con el valor de retorno adecuado.

