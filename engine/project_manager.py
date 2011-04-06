# encoding: UTF-8
import psycopg2
import model
import binascii
import hashlib
import os , os.path

from bjsonrpc.exceptions import ServerError
from bjsonrpc.handlers import BaseHandler
from base64 import b64encode, b64decode
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
    
    def __str__(self):
        #return repr(self.getSignature(list("+/0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"), style = "text"))
        return repr(self.getHashList(["++"]))
        
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
            
    def getHashList(self, keylist = [""]):
        hashlist = set([])
        for key in keylist:
            hashes = set(self._get_hash_list(key, self.index))
            hashlist|= hashes
        
        hashdict = {}
        for mhash in hashlist:
            hashdict[mhash] = b64digest_namecache[mhash]
             
        return hashdict
    
    def getSignature(self, keylist = [""], style = "list", hashsize = 10, hashoffset = 0):
        retlist = []
        for key in keylist:
            pos = len(key)
            hashlist = self._get_hash_list(key, self.index)
            hashoptions = self._get_hash_options(key, self.index)
            digest = get_b64digest("".join(hashlist))[hashoffset:hashoffset+hashsize]
            size = len(hashlist)
            retlist.append([key,size,"".join(hashoptions),digest])
        
        if style == "list":
            return retlist
        elif style == "text":
            textdigest = ""
            for key,size,options,digest in retlist:
                textdigest += digest
            return textdigest
        else: raise ValueError, "unknown style."

class ProjectManager(BaseHandler):
    def __init__(self, rpc, prj,user, conn):
        BaseHandler.__init__(self,rpc)
        self.data = prj
        self.path = prj.path
        self.user = user
        self.conn = conn
        self.rpc = rpc
        self.cachehashsize = 4
        self.cachehashoffset = 0
        self._load()
        
    def _load(self):
        print "Loading . . . " , self.data
        self.cur = self.conn.cursor()
        self.filelist = {}
        #self.filehash = {}
        #self.filecache = {}
        #self.treecache = {}
        self.b64list = HashTable(self.rpc)
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
                self.filelist[relroot] = files
                for name in files:
                    fullpath = os.path.join(root,name)
                    key = relroot+"/"+name
                    b64digest = get_file_b64digest(fullpath, name = key)
                    self.b64list.add(b64digest)
                    """
                    microhash = b64digest[self.cachehashoffset:self.cachehashoffset+self.cachehashsize]
                    
                    if microhash not in self.filecache:
                        self.filecache[microhash] = set([])
                        
                    if microhash[0] not in self.treecache:
                        self.treecache[microhash[0]] = set([])
                    
                    
                    digests.add(b64digest)
                    self.treecache[microhash[0]].add(b64digest)
                    self.filecache[microhash].add(key)
                    if b64digest not in self.filehash: 
                        self.filehash[b64digest] = set([])
                    self.filehash[b64digest].add(key)
                    """
                    #print key, hashdigest
        print self.b64list
        """
        print "signature:", get_b64digest("".join(sorted(self.filehash.keys())))
        
        
        microsignature = ""
        sz = 10
        for key1, mhashlist in sorted(self.treecache.iteritems()):
            microsignature += key1
            microsignature += get_b64digest("".join(sorted(list(mhashlist))))[:sz]
            #print "signature for '%s': %s" % (key1,get_b64digest("".join(sorted(list(mhashlist)))))
        print ":%d:%s" %(sz,microsignature)
        for key in self.treecache:
            microsignature2 = key + ":"
            for mhash in sorted(list(self.treecache[key])):
                microsignature2 += mhash[1:1+sz]
            print microsignature2
        """
        #for k in sorted(self.filehash.keys()):
        #    print k, " ".join(sorted(list(self.filehash[k])))
            
        #print
        #print "---"
        #collisions = len(digests) - len(self.filecache.keys())
        #print "%d digests, %d microkeys" % (len(digests),len(self.filecache.keys()))
        #print "%d collisions (%.2f%%)" % (collisions,float(collisions)/len(digests)*100.0)
        #totalbytes = 0
        #for key1, mhashlist in sorted(self.treecache.iteritems()):
        #    if mhashlist:
        #        bytes = 1+len(list(mhashlist)[0])*len(mhashlist)
        #        print key1, len(mhashlist), bytes, " ".join(sorted(list(mhashlist)))
        #        totalbytes += bytes
        #    
        #print "total bytes:", totalbytes
        #print "---"
        #print 
    
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
        return {"." : self.filelist["."]}
        

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
    