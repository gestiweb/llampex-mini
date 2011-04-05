# encoding: UTF-8
import psycopg2
import model
from bjsonrpc.exceptions import ServerError

class ProjectManager(object):
    def __init__(self, prj):
        self.data = prj
        self.load()
        
    def load(self):
        print "Loading . . . " , self.data
        
def login(project,username,password):
    print "connecting to project", project
    print "as user", username
    if project.host is None: project.host = model.engine.url.host
    if project.port is None: project.port = model.engine.url.port
    if project.user is None: project.user = model.engine.url.username
    if project.password is None: project.password = model.engine.url.password
        
    try:
        conn = psycopg2.connect(
                database = project.db,
                user = project.user,
                password = project.password,
                host = project.host,
                port = project.port
            )
        if not conn:
            raise ValueError, "connection invalid!"
            
    except psycopg2.OperationalError, e:
        print e.__class__.__name__, repr(e.args[:])
        raise ServerError,"DatabaseConnectionError"
            
    except Exception, e:
        print e.__class__.__name__, repr(e.args[:])
        raise ServerError, "Some unknown error ocurred trying to connect to the project. Check logs at server."
    
    projectmanager = None
    
    try:
        cur = conn.cursor() 
        try:
            cur.execute("SELECT iduser,username,password FROM users WHERE username = %s;", [username])
        except psycopg2.ProgrammingError,e:
            print e.__class__.__name__, repr(e.args[:])
            print "Check if 'users' table exists."
            raise ServerError,"DatabaseConnectionError"
            
        userrow = cur.fetchone()
        if userrow is None: raise ServerError, "LoginInvalidError"
        iduser, username, password = userrow
        
    finally:
        cur.close()
        if projectmanager is None:
            conn.close()
            
    
