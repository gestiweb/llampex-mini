# encoding: UTF-8
import psycopg2
import model
import binascii
import hashlib
import os , os.path

from bjsonrpc.exceptions import ServerError
from bjsonrpc.handlers import BaseHandler

verbose = False

class ProjectManager(BaseHandler):
    def __init__(self, rpc, prj,user, conn):
        BaseHandler.__init__(self,rpc)
        self.data = prj
        self.path = prj.path
        self.user = user
        self.conn = conn
        self._load()
        
    def _load(self):
        print "Loading . . . " , self.data
        self.cur = self.conn.cursor()
        self.filelist = {}
        self.filehash = {}
        for root, dirs, files in os.walk(self.path):
            relroot = root[len(self.path):]
            if relroot.startswith("/"):
                relroot = relroot[1:]
            if relroot == "": relroot = "."
            
            for name in files[:]: 
                if name.startswith("."):
                    files.remove(name)
            for name in dirs[:]: 
                if name.startswith("."):
                    dirs.remove(name)
            if files:
                self.filelist[relroot] = files
                for name in files:
                    fullpath = os.path.join(root,name)
                    hashdigest = hashlib.sha1(open(fullpath).read()).hexdigest()
                    key = relroot+"/"+name
                    self.filehash[key] = hashdigest
                    print key, hashdigest
        
    
    def getUserList(self):
        self.cur.execute("SELECT iduser,username FROM users ORDER BY iduser")
        retlist = []
        for row in self.cur:
            retlist.append({
                "id": row[0],
                "name" : row[1],
            })
            
        return retlist
        
    def getFileList(self):
        return self.filelist
        

def login(rpc,project,username,password):
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
        iduser, dbusername, dbpassword = userrow
        if not validate_password(password, dbpassword): raise ServerError, "LoginInvalidError"
        projectmanager = ProjectManager(rpc, project, dbusername, conn)
        return projectmanager
    finally:
        cur.close()
        if projectmanager is None:
            conn.close()
            
def validate_password(userpass, dbpass):
    hashmethod, hashsalt, hashdigest = dbpass.split("$")
    if hashmethod in ("md5","sha1"):
        binsalt = binascii.a2b_hex(hashsalt)
        userdigest = compute_password_hexhash(userpass, hashmethod, binsalt)
    else:
        print "Unknown hashmethod %s" % repr(hashmethod)
        return False
        
    if userdigest == hashdigest: return True
    if verbose:
        print "Password validation failed:"
        print "User supplied:", userdigest
        print "Database supplied:", hashdigest
        
    return False

def compute_password(userpass, hashmethod, saltsize = 4):
    hashsalt = hashlib.sha1(userpass + hashmethod + os.urandom(32)).hexdigest()[:saltsize*2]
    if hashmethod in ("md5","sha1"):
        binsalt = binascii.a2b_hex(hashsalt)
        userdigest = compute_password_hexhash(userpass, hashmethod, binsalt)
    else:
        print "Unknown hashmethod %s" % repr(hashmethod)
        return False
    return "$".join([hashmethod,hashsalt,userdigest])    
    
        
def compute_password_hexhash(userpass, hashmethod, binsalt):
    saltedpass = binsalt + userpass
    m = None
    if hashmethod == "md5":
        m = hashlib.md5()
    elif hashmethod == "sha1":
        m = hashlib.sha1()
    else:
        raise ValueError, "Unsupported hashmethod '%s' " % repr(hashmethod)
        
    m.update(saltedpass)
    userdigest = m.hexdigest()
    return userdigest
    