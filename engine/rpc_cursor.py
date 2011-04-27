# encoding: UTF-8
import threading
# UNICODE HANDLING:
#  In Python 2, if you want to receive uniformly all your database input in 
#  Unicode, you can register the related typecasters globally as soon as 
#  Psycopg is imported:
import psycopg2
import psycopg2.extensions
psycopg2.extensions.register_type(psycopg2.extensions.UNICODE)
psycopg2.extensions.register_type(psycopg2.extensions.UNICODEARRAY)

from bjsonrpc.exceptions import ServerError
from bjsonrpc.handlers import BaseHandler

def tuplenormalization(rows):
    retrows = []
    for row in rows:
        retrow = []
        for field in row:
            if field is None:
                retfield = None
            elif type(field) is bool:
                retfield = field
            else:
                retfield = unicode(field)
            retrow.append(retfield)
        retrows.append(retrow)
    return retrows
    

def withrlock(function):
    def lockfn(self,*args,**kwargs):
        if self.cur is None: raise ServerError, "Cursor not Open!"
        self.rlock.acquire()
        ret = function(self,*args,**kwargs)
        self.rlock.release()
        return ret

    lockfn.__name__ = function.__name__
    return lockfn
        


class RPCCursor(BaseHandler):
    globaldata = { 'cursornumber' : 1 }
    def __init__(self, rpc, prjmanager):
        BaseHandler.__init__(self,rpc)
        self.pm = prjmanager
        cursornumber = self.globaldata['cursornumber']
        self.globaldata['cursornumber'] += 1
        self.curname = "rpccursor_%04x" % cursornumber
        self.cur = self.pm.conn.cursor()
        self.rlock = threading.RLock()

    @withrlock    
    def description(self):
        "Returns field properties"
        return self.cur.description

    @withrlock    
    def fields(self):
        "Returns field list"
        descrip = self.cur.description
        if descrip is None: return None
        fields = [l[0] for l in descrip]
        return fields
    
    @withrlock    
    def commit(self):
        "Commits the current transaction."
        self.pm.conn.commit()
    
    @withrlock    
    def rollback(self):
        "Rollbacks the changes for the current transaction."
        self.pm.conn.rollback()
    
    @withrlock    
    def close(self):
        "Closes the cursor."
        self.cur.close()
        self.pm.cursors.remove(self)
        self.cur = None
        BaseHandler.close(self)
        
    @withrlock    
    def execute(self, sql, params = None):
        "Executes the specified SQL with given parameters."
        if params:
            return self.cur.execute(sql,params)
        else:
            return self.cur.execute(sql)

    @withrlock    
    def fetch(self, size=20):
        "Fetches many rows. Use -1 or None for querying all available rows."
        if size is None or size <= 0:
            return tuplenormalization(self.cur.fetchall())
        else:
            return tuplenormalization(self.cur.fetchmany(size))
        
    @withrlock    
    def scroll(self, value, mode = 'relative'):
        """Moves the cursor up and down specified by *value* rows. mode can be
        set to 'absoulte'. """
        try:
            return self.cur.scroll(value, mode)
        except (psycopg2.ProgrammingError, IndexError), e:
            return None
        
    @withrlock    
    def rowcount(self):
        "Returns the count of rows for the last query executed."
        return self.cur.rowcount
        
    @withrlock    
    def rownumber(self):
        "Return the row index where the cursor is in a zero-based index."
        return self.cur.rownumber
        
    @withrlock
    def query(self):
        "Return the latest SQL query sent to the backend"
        return self.cur.query
        
    @withrlock
    def statusmessage(self):
        "Return the latest Status message returned by the backend"
        return self.cur.query
    
    @withrlock
    def copy_from(self,*args):
        "Coipes a data set from a file to the server"
        raise ServerError, "NotImplementedError"
    
    @withrlock
    def copy_to(self,*args):
        "Dumps a data set from table to a file"
        raise ServerError, "NotImplementedError"
        
    
    