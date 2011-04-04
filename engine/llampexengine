#!/usr/bin/env python
# encoding: UTF-8
from optparse import OptionParser
from database import connect, create_all
import engine

global options
options = None

def main():
    global options
    parser = OptionParser()
    parser.set_defaults(
            dbname = "llampex",
            dbuser = "llampexuser",
            dbpasswd = "llampexpasswd",
            dbhost = "127.0.0.1",
            dbport = 5432,
            createtables = False
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
    