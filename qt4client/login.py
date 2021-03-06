#!/usr/bin/env python
# encoding: UTF-8
import sys
import os.path
import time, threading, traceback
import yaml, hashlib, bz2, zlib
from base64 import b64decode, b64encode

try:
    from PyQt4 import QtGui, QtCore, QtSql, uic
except ImportError:
    print "ERROR: Unable to import PyQt4 (Qt4 for Python)."
    print " * * * Please install PyQt4 / python-qt4 package * * *"    
    sys.exit(1)

try:
    import bjsonrpc
except ImportError:
    print "ERROR: Unable to import bjsonrpc (bidirectional JSON-RPC protocol)."
    print " * * * Please install bjsonrpc package * * *"    
    sys.exit(1)

bjsonrpc_required_release = '0.2.0'
try:
    assert(bjsonrpc.__release__ >= bjsonrpc_required_release)
except AssertionError:
    print "ERROR: bjsonrpc release is %s , and llampex mini qt4client requires at least %s" % (bjsonrpc.__release__, bjsonrpc_required_release)
    print " * * * Please Upgrade BJSONRPC * * * "
    sys.exit(1)
from bjsonrpc.exceptions import ServerError
import qsqlrpcdriver.qtdriver as qtdriver

from mainwindow import LlampexMainWindow
from widgets import llampexmainmenu
from manage_dialog import ManageDialog

__version__ = "0.0.1"
diskwrite_lock = threading.Lock()
lampex_icon = None

def apppath(): return os.path.abspath(os.path.dirname(sys.argv[0]))
def filepath(): return os.path.abspath(os.path.dirname(__file__))

def appdir(x): # convierte una ruta relativa a la aplicación en absoluta
    if os.path.isabs(x): return x
    else: return os.path.join(apppath(),x)
def filedir(x): # convierte una ruta relativa a este fichero en absoluta
    if os.path.isabs(x): return x
    else: return os.path.join(filepath(),x)

def argvparam(key):
    try:
        idx = sys.argv.index("-"+key)
    except ValueError:
        return None
    
    try:
        value = sys.argv[idx+1]
    except IndexError:
        return ""
    
    return value
    
def str2bool(x):
    if x == "": return False
    x = x.lower()[0]
    if x == "0": return False
    if x == "f": return False
    if x == "n": return False
    if x == "1": return True
    if x == "y": return True
    if x == "t": return True
    
    

class ConfigSettings(yaml.YAMLObject):
    yaml_tag = u'!ConfigSettings' 
    
    def setargv(self, key, default = None, cast=str):
        val = argvparam(key)
        if val is not None: 
            setattr(self,key,cast(val))
        else:
            if not hasattr(self,key):
                setattr(self,key,default)
                
    @classmethod
    def load(cls, filename=".settings.yaml"):
        try:
            f1 = open(filedir(filename),"r")
            settings = yaml.load(f1.read())
        except IOError:
            settings = ConfigSettings()
        settings.setDefaults()
        return settings
    
    def setDefaults(self):
        self.setargv("username","")
        self.setargv("password","")
        self.setargv("host","127.0.0.1")
        self.setargv("port","10123")
        self.setargv("remember",False, cast=str2bool)
        self.setargv("debug",False, cast=str2bool)
        self.setargv("project","")
    
    
    

class ConnectionDialog(QtGui.QDialog):
    def __init__(self):
        QtGui.QDialog.__init__(self)
            
        ui_filepath = filedir("forms/login.ui") # convertimos la ruta a absoluta
        self.ui = uic.loadUi(ui_filepath,self) # Cargamos un fichero UI externo    
        global llampex_icon 
        llampex_icon = self.windowIcon()
        settings = ConfigSettings.load()
        self.project = settings.project
        self.debug = settings.debug
        self.ui.user.setText(settings.username)
        self.ui.password.setText(settings.password)
        try:
            self.ui.host.setText(settings.host)
            self.ui.port.setText(settings.port)
        except Exception:
            pass
        self.ui.rememberpasswd.setChecked(settings.remember)
        self.connect(self.ui.manage, QtCore.SIGNAL("clicked()"), self.manage_clicked)
        selected = 0
        if '-autoconnect' in sys.argv: 
            QtCore.QTimer.singleShot(10,self.accept)

        """
        availableprojects  = c.call.getAvailableProjects()
        for row,rowdict in enumerate(availableprojects):
            listitem = QtGui.QListWidgetItem("%(description)s (%(code)s)" % rowdict)
            listitem.project = rowdict
            if rowdict['code'] == settings.project: selected = row
            self.ui.project.addItem(listitem)
        self.ui.project.setCurrentRow(selected)
        """    
    def manage_clicked(self):
        host = unicode(self.ui.host.text())
        port = unicode(self.ui.port.text())
        port = int(port)
        
        try:
            self.conn = bjsonrpc.connect(host=host,port=port)
            self.conn._debug_socket = self.debug
        except Exception, e:
            msgBox = QtGui.QMessageBox()
            msgBox.setText("Error trying to connect to %s:%d: %s: %s\n" % (host,port,e.__class__.__name__ ,repr(e.args)))
            msgBox.setIcon(QtGui.QMessageBox.Critical)
            msgBox.exec_()
            return
        
        global managewindow
        managewindow = ManageDialog(self.conn, filedir("forms/manage.ui"), filedir("forms/addProject.ui"))
        managewindow.show()
        self.close()
        
    def accept(self):
        username = unicode(self.ui.user.text())
        password = unicode(self.ui.password.text())
        host = unicode(self.ui.host.text())
        port = unicode(self.ui.port.text())
        try:
            port = int(port)
        except ValueError:
            msgBox = QtGui.QMessageBox()
            msgBox.setText("The port number must be integer")
            msgBox.setIcon(QtGui.QMessageBox.Critical)
            msgBox.exec_()
            return
            
        try:
            self.conn = bjsonrpc.connect(host=host,port=port)
            self.conn._debug_socket = self.debug
        except Exception, e:
            msgBox = QtGui.QMessageBox()
            msgBox.setText("Error trying to connect to %s:%d: %s: %s\n" % (host,port,e.__class__.__name__ ,repr(e.args)))
            msgBox.setIcon(QtGui.QMessageBox.Critical)
            msgBox.exec_()
            return
            
        try:            
            logresult = self.conn.call.login(username,password)
            if not logresult: raise ValueError
            global selectionwindow
            selectionwindow = ProjectSelectionDialog(self.conn)
            
            availableprojects  = self.conn.call.getAvailableProjects()
            if len(availableprojects) == 1:
                print "Only 1"
                for row,rowdict in enumerate(availableprojects):
                    self.project = rowdict['code']
            else:
                print "Multiple or None"
                selectionwindow.show()
            
            if self.project:
                selectionwindow.open_project(self.project)
            self.close()
            return
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
        settings.host = str(self.ui.host.text())
        settings.port = str(self.ui.port.text())
        if self.ui.rememberpasswd.isChecked():
            settings.username = str(self.ui.user.text())
            settings.password = str(self.ui.password.text())
            settings.remember = True
        else:
            settings.username = ""
            settings.password = ""
            settings.remember = False
        f1 = open(filedir(".settings.yaml"),"w")
        f1.write(yaml.dump(settings))
        event.accept()
        #event.ignore()      

class ProjectSelectionDialog(QtGui.QDialog):
    def __init__(self, conn):
        QtGui.QDialog.__init__(self)
        self.setWindowTitle("Project selection")
        self.resize(500,300)
        self.conn = conn
        availableprojects  = self.conn.call.getAvailableProjects()
        self.layout = QtGui.QVBoxLayout()
        self.setWindowIcon(llampex_icon)

        n = 0
        for row,rowdict in enumerate(availableprojects):
            n += 1
            button = llampexmainmenu.LlampexMainMenuButton("%(code)s" % rowdict, rowdict['code'],self.open_project)
            button.setDescription("%(description)s" % rowdict)
            button.setMaximumHeight(96)
            self.layout.addWidget(button)
            
        if n == 0:
            label = QtGui.QLabel("No projects available for this username")
            self.layout.addWidget(label)
        
        self.setLayout(self.layout)
        
    def open_project(self,projectname):
        print "Open", projectname
        project_manager = self.conn.call.connectProject(projectname)
        splashwindow = SplashDialog()
        splashwindow.prjname = projectname
        splashwindow.prjconn = project_manager
        splashwindow.show()
        self.close()
        
        
    
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
        self.prjname = None
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
            "end" : 2000,
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
            pparts = {}
            for i,k in enumerate(self.rprj.project_childs):
                pparts[k] = self.rprj.filetree.method.getNodeHashValue([k])
            
            for i,k in enumerate(pparts):
                p = i*100/sz
                self.status_extra = "%d%%" % (p)
                self.progress_extra = p
                nodevalues = pparts[k].value
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
            cachedir = filedir(".cache/%s/files" % self.prjname)
            self.projectpath = cachedir
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
        if not hasattr(self.prjconn,"qtdriver"):
            qtdriver.DEBUG_MODE = True
            self.prjconn.qtdriver = qtdriver.QSqlLlampexDriver(self.prjconn)
            self.prjconn.qtdb = QtSql.QSqlDatabase.addDatabase(self.prjconn.qtdriver, "llampex-qsqlrpcdriver")
            assert(self.prjconn.qtdb.open("",""))
            qtdriver.DEBUG_MODE = False
        
        mainwin = LlampexMainWindow(self.projectpath, self.rprj.files,self.prjconn)
        mainwin.setWindowIcon(llampex_icon)
        mainwin.show()
        self.close()
        

    
def get_b64digest(text):
    bindigest = hashlib.sha1(text).digest()
    b64digest = b64encode(bindigest)[:20]
    return b64digest

"""    
try:        
    import formimages
except ImportError:
    print "formimages.py not found. Probably you forgot to do 'pyrcc forms/..qrc -i formimages.py'"
"""
def main():
    app = QtGui.QApplication(sys.argv) # Creamos la entidad de "aplicación"

    # Iniciar como: python login.py -stylesheet styles/llampex1/style.css
    # app.setStyleSheet(open(filedir("styles/llampex1/style.css")).read())

    connwindow = ConnectionDialog()
    connwindow.show() # el método show asegura que se mostrará en pantalla.


    retval = app.exec_() # ejecutamos la aplicación. A partir de aquí perdemos el

    sys.exit(retval) # salimos de la aplicación con el valor de retorno adecuado.

if __name__ == "__main__": main()