# encoding: UTF-8
import psycopg2
import model
import binascii
import hashlib, threading
import os , os.path, bz2, zlib
import yaml

from bjsonrpc.exceptions import ServerError
from bjsonrpc.handlers import BaseHandler
from base64 import b64encode, b64decode
import rpc_cursor
import qsqlrpcdriver.servercursor as servercursor

verbose = False
b64digest_filecache = {}
b64digest_namecache = {}

def get_b64digest(text):
    bindigest = hashlib.sha1(text).digest()
    b64digest = b64encode(bindigest)[:20]
    return b64digest


def get_file_b64digest(filename, name):
    mtime = os.stat(filename).st_mtime
    if filename in b64digest_filecache:
        mtime2, b64digest2 = b64digest_filecache[filename]
        if mtime == mtime2:
            return b64digest2
    f1 = open(filename)
    filetext = f1.read()
    text_b64digest = get_b64digest(filetext)
    name_b64digest = get_b64digest(name)
    b64digest = get_b64digest(name_b64digest + text_b64digest)
    b64digest_namecache[b64digest] = {'name': name, 'digest':text_b64digest}
    b64digest_filecache[filename] = (mtime, b64digest )
    return b64digest

class HashTable(BaseHandler):
    def __init__(self, rpc):
        BaseHandler.__init__(self,rpc)
        self.hashlist = []
        self.index = {}
        self.index_maxdepth = 2
        self.b64tr1 = "+/0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
        self.b64tr2 = {}
        for n,c in enumerate(list(self.b64tr1)):
            self.b64tr2[c] = n/8
        
    def add(self,key):
        self.hashlist.append(key)
        
        self._addindex(key, key, self.index)
    
    def _addindex(self, key, value, index, depth = 1):
        k = key[0]
        if depth < self.index_maxdepth:
            if k not in index:
                index[k] = {}
            self._addindex(key[1:], value, index[k], depth + 1)
        else:
            if k not in index:
                index[k] = []
            index[k].append(value)

       
    def _get_hash_index(self,index):
        if type(index) is list:
            return index
        if type(index) is dict:
            retlist = []
            for k,ilist in index.iteritems():
                retlist += self._get_hash_index(ilist)
            return retlist
    
    def _get_hash_list(self, key, index, pos = 0):
        if len(key) <= pos:
            return self._get_hash_index(index)
        if type(index) is list:
            return [ ilist for ilist in index if ilist.startswith(key) ]
        if type(index) is dict:
            k = key[pos]
            if k not in index: return []
            else:
                return self._get_hash_list(key,index[k],pos+1)
    
    def _get_hash_options(self, key, index, pos = 0):
        if len(key) > pos: # advance to find the correct options.
            if type(index) is dict:
                k = key[pos]
                if k not in index: return []
                return self._get_hash_options(key,index[k],pos+1)
        # final position, or end-of-index, return possible option-letters.
        if type(index) is dict: # final position and not endofindex.
            return sorted(index.keys())
        # end of index. manually get choices or return empty.
        return []
            
    def _get_node_hash_list(self, keylist = [""], style = "dict", hashsize = 10, hashoffset = 0):
        hashlist = set([])
        for key in keylist:
            hashes = set(self._get_hash_list(key, self.index))
            hashlist|= hashes
        if style == "dict":
            hashdict = {}
            for mhash in hashlist:
                hashdict[mhash] = b64digest_namecache[mhash]
            return hashdict
        elif style == "list":
            hlist = [ mhash[hashoffset:hashoffset+hashsize] for mhash in sorted(list(hashlist))]
            return hlist
        else: raise ValueError, "unknown style."

        
    def getNodeSignature(self, parentkey = "", hashsize = 20, hashoffset = 0):
        return self._get_signature([parentkey],"list",hashsize,hashoffset)[0]

    def getChild8Signature(self, parentkey = "", hashsize = 10, hashoffset = 0):
        hashoptions = self._get_hash_options(parentkey, self.index)
        keylist = [ parentkey + opt for opt in hashoptions ]
        signdict = self._get_signature(keylist,"dict",hashsize,hashoffset)
        child8 = [[],[],[],[],[],[],[],[]]
        for k, val in signdict.iteritems():
            k8 = self.b64tr2[k[-1]]
            child8[k8].append(val)
        
        child8_2 = []
        for v in child8:
            child8_2.append(get_b64digest("".join(v)))
        return child8_2
    
    def getChildSignature(self, parentkey = "", hashsize = 10, hashoffset = 0):
        hashoptions = self._get_hash_options(parentkey, self.index)
        keylist = [ parentkey + opt for opt in hashoptions ]
        return self._get_signature(keylist,"dict",hashsize,hashoffset)
    
    def getNodeHashList(self, keylist, hashsize = 10, hashoffset = 0):
        return self._get_node_hash_list(keylist, "list", hashsize, hashoffset)

    def getNodeHashValue(self, keylist):
        if isinstance(keylist,basestring):
            keylist = [keylist]
        return self._get_node_hash_list(keylist, "dict",20,0)
    
    def _get_signature(self, keylist = [""], style = "list", hashsize = 20, hashoffset = 0):
        retlist = []
        for key in keylist:
            pos = len(key)
            hashlist = self._get_hash_list(key, self.index)
            hashoptions = self._get_hash_options(key, self.index)
            digest = get_b64digest("".join(hashlist))[hashoffset:hashoffset+hashsize]
            size = len(hashlist)
            retlist.append([key,size,digest])
        
        if style == "list":
            return retlist
        elif style == "text":
            textdigest = ""
            for key,size,digest in retlist:
                textdigest += key+digest
            return textdigest
        elif style == "dict":
            textdigest = {}
            for key,size,digest in retlist:
                textdigest[key] = digest
            return textdigest
        else: raise ValueError, "unknown style."

class ProjectManager(BaseHandler):
    def __init__(self, rpc, prj, user, conn):
        BaseHandler.__init__(self,rpc)
        self.data = prj
        self.path = prj.path
        self.user = user
        self.conn = conn
        self.rpc = rpc
        self.cachehashsize = 4
        self.cachehashoffset = 0
        self.filelist = {}
        #self.filehash = {}
        #self.filecache = {}
        #self.treecache = {}
        self.b64list = HashTable(self.rpc)
        self.is_loaded = False
        self.load_thread = threading.Thread(target=self._load)
        self.load_thread.start()
        self.cursors = []
        
    def newCursor(self):
        newcur = rpc_cursor.RPCCursor(self.rpc, self)
        self.cursors.append(newcur)
        return newcur
        
    def getCursor(self):
        return servercursor.CursorSQL(self)
            
    def isLoaded(self): 
        return self.is_loaded    
    
    def _load(self):
        print "Loading . . . " , self.data
        digests = set([])
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
                for name in files:
                    if name.endswith(".llampexcache"): continue
                    fullpath = os.path.join(root,name)
                    key = relroot+"/"+name
                    self.filelist[key] = fullpath
                    b64digest = get_file_b64digest(fullpath, name = key)
                    self.b64list.add(b64digest)
        self.is_loaded = True
        print "project loaded."
        """
        print
        from bjsonrpc.jsonlib import dumps

        print
        print "** Get global signature and options :::"
        print dumps( self.b64list.getNodeSignature(), self._conn)
        print
        print "** Get signature for each 1/64 part :::"
        print dumps( self.b64list.getChildSignature() , self._conn)
        print
        print "** Get signature for each 1/8 part for '+' :::"
        print dumps( self.b64list.getChild8Signature("+") , self._conn)
        print
        print "** Get all hashes for '+%' part 0 :::"
        print dumps( self.b64list.getNodeHashList([ "+" + opt for opt in "+/012345"]) , self._conn)
        print
        print "** Get all hashes for 'zc%' 'zD%' :::"
        print dumps( self.b64list.getNodeHashValue(["zc","zD"]) , self._conn)
        print
        """
        
    def getFileName(self,filename):
        if filename not in self.filelist:
            return None
        fullpath = self.filelist[filename]
        pathhead, pathtail = os.path.split(fullpath)
        cachepath = os.path.join(pathhead, ".%s.llampexcache" % pathtail)
        mtime = os.stat(fullpath).st_mtime
        
        try:
            mtime2 = os.stat(cachepath).st_mtime
            if mtime2 < mtime: raise ValueError

            f1 = open(cachepath)
            zipcontent = f1.read()
            f1.close()
        except Exception:    
            print "creating cache for", filename
            filecontent = open(fullpath).read()
            zipcontent = bz2.compress(filecontent,9)
            f1 = open(cachepath,"w")
            f1.write(zipcontent)
            f1.close()
            
        
        b64content = b64encode(zipcontent)
        return b64content
    
    def getFileTree(self):
        return self.b64list
    
    def getDirectLinks(self):
        links = None
        try:
            config = model.session.query(
                model.RowUserConfig).filter(model.RowUserConfig.user==self.user).filter(
                model.RowUserConfig.project==self.data.code).filter(
                model.RowUserConfig.configname=="directlinks").one()
            
            links = yaml.load(config.value)
        except:
            links = []
        
        return links
    
    def updateDirectLinks(self,links):
        config = None
        try:
            config = model.session.query(
                model.RowUserConfig).filter(model.RowUserConfig.user==self.user).filter(
                model.RowUserConfig.project==self.data.code).filter(
                model.RowUserConfig.configname=="directlinks").one()
        except:
            config = model.RowUserConfig()
            config.user = self.user
            config.project = self.data.code
            config.configname = "directlinks"
            model.session.add(config)
             
        config.value = yaml.dump(links)
        model.session.commit()

def connect_project(rpc,project,username):
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
    
    projectmanager = ProjectManager(rpc, project, username, conn)
    return projectmanager
    
            
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

def compute_password(userpass, hashmethod = "sha1", saltsize = 4):
    hashsalt = hashlib.sha1(userpass + hashmethod + os.urandom(32)).hexdigest()[:saltsize*2]
    if hashmethod in ("md5","sha1"):
        binsalt = binascii.a2b_hex(hashsalt)
        userdigest = compute_password_hexhash(userpass, hashmethod, binsalt)
    else:
        print "Unknown hashmethod %s" % repr(hashmethod)
        return False
    return "$".join([hashmethod,hashsalt,userdigest])    
    
        
def compute_password_hexhash(userpass, hashmethod, binsalt):
    saltedpass = binsalt + str(userpass)
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
    
