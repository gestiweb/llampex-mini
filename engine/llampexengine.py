#!/usr/bin/env python
# encoding: UTF-8
from optparse import OptionParser
from database import connect, create_all
from config import Config
import engine
import sys

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
    print "ERROR: bjsonrpc release is %s , and llampex engine requires at least %s" % (bjsonrpc.__release__, bjsonrpc_required_release)
    print " * * * Please Upgrade BJSONRPC * * * "
    sys.exit(1)


global options
options = None

def main():
    global options
    parser = OptionParser()
    parser.set_defaults(
            dbname = Config.Database.dbname,
            dbuser = Config.Database.dbuser,
            dbpasswd = Config.Database.dbpasswd,
            dbhost = Config.Database.dbhost,
            dbport = Config.Database.dbport,
            createtables = Config.Database.createtables
            )
            
    parser.add_option("--dbname", dest="dbname",
                      help="PostgreSQL database to connect the Llampex Engine", metavar="DBNAME")
    parser.add_option("--host", dest="dbhost",
                      help="PostgreSQL host to connect", metavar="DBHOST")
    parser.add_option("--port", dest="dbport", type="int",
                      help="PostgreSQL port to connect", metavar="DBPORT")
    parser.add_option("--user", dest="dbuser",
                      help="PostgreSQL User", metavar="DBUSER")
    parser.add_option("--pass", dest="dbpasswd",
                      help="PostgreSQL Password for User", metavar="DBUSER")
    parser.add_option("--createtables", dest="createtables", action="store_true",
                      help="Creates the needed tables if aren't in the database yet")
                      

    (options, args) = parser.parse_args()
    dboptions = {}
    for key in dir(options):
        if key.startswith("db"):
            dboptions[key] = getattr(options,key)
    connect(dboptions)
    if options.createtables:
        create_all()
        
    engine.start()
    engine.wait()
    
if __name__ == "__main__":
    main()
    