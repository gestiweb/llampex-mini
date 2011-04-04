import model
from model import RowProject
from project_manager import ProjectManager

import bjsonrpc
from bjsonrpc.handlers import BaseHandler

import threading
import signal

import signal, os

thread_server = None

class ServerHandler(BaseHandler):
    def getAvailableProjects(self):
        return []

def handler(signum, frame):
    print 'Received signal number', signum
    raise KeyboardInterrupt

def start():
    global thread_server
    #signal.signal(signal.SIGINT, handler)
    server = bjsonrpc.createserver(host="0.0.0.0", port=10123, handler_factory=ServerHandler)        
    thread_server = threading.Thread(target=server.serve)
    thread_server.daemon = True
    thread_server.start()
    
    # projectrows = model.session.query(RowProject).filter(RowProject.active == True)
    projectrows = model.session.query(RowProject).filter_by(active = True)
    for rowproject in projectrows:
        ProjectManager(rowproject)
        

def wait():
    if thread_server:
        try:
            while True:
                thread_server.join(1)
        except KeyboardInterrupt:
            print "bye!"
        
        

    
