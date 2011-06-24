import model
from model import RowProject, RowUser,RowProjectUser

import project_manager
import manage_projects

import bjsonrpc
from bjsonrpc.handlers import BaseHandler
from bjsonrpc.exceptions import ServerError

import threading

import signal, os

thread_server = None

class ServerHandler(BaseHandler):
    username = None
    def getAvailableProjects(self):
        if self.username is None: raise ServerError, "LoginInvalidError"
        projectlist = []
        projectrows = model.session.query(RowProject).filter(RowProject.active == True).filter(RowProject.id.in_(model.session.query(RowProjectUser.project_id).filter(RowProjectUser.user_id == self.user.id))).order_by(RowProject.code)
        for rowproject in projectrows:
            projectrow = {
                'code' : rowproject.code,
                'description' : rowproject.description,
                }
            projectlist.append(projectrow)
        return projectlist
    
    def login(self,username,password):
        if self.username is not None: raise ServerError, "AlreadyLoggedError"
        userrow = model.session.query(RowUser).filter_by(active = True,username = username).first()
        if userrow is None: raise ServerError, "LoginInvalidError"
        
        if not project_manager.validate_password(password, userrow.password): raise ServerError, "LoginInvalidError"
        #projectmanager = ProjectManager(rpc, project, dbusername, conn)
        #return projectmanager
        self.username = username
        self.user = userrow
        return True
        
        
    def connectProject(self,projectname):
        if self.username is None: raise ServerError, "LoginInvalidError"
        
        projectrow = model.session.query(RowProject).filter_by(code = projectname).first()
        if projectrow is None:
            raise ServerError, "No project exists with the name '%s'" % projectname
        if projectrow.active != True:
            raise ServerError, "Project '%s' is not active" % projectname
        # TODO: Limit user access for this project
        
        return project_manager.connect_project(self,projectrow, self.username)
        
    def getManageProjects(self):        
        return manage_projects.getManageProjects(self)
        
        

def handler(signum, frame):
    print 'Received signal number', signum
    raise KeyboardInterrupt

def start(verbose = False):
    global thread_server
    #signal.signal(signal.SIGINT, handler)
    rpcserver = bjsonrpc.createserver(host="0.0.0.0", port=10123, handler_factory=ServerHandler)        
    rpcserver.debug_socket(verbose)
    thread_server = threading.Thread(target=rpcserver.serve)
    thread_server.daemon = True
    thread_server.start()
    
    # projectrows = model.session.query(RowProject).filter(RowProject.active == True)
    #projectrows = model.session.query(RowProject).filter_by(active = True)
    #for rowproject in projectrows:
    #    ProjectManager(rowproject)
        

def wait():
    if thread_server:
        try:
            while True:
                thread_server.join(1)
        except KeyboardInterrupt:
            print "bye!"
        
        

    
