# coding: UTF8
from autoconfig.autoconfig import AutoConfigTemplate, ConfigReader
import sys, os.path

def filepath(): return os.path.abspath(os.path.dirname(__file__))
def filedir(x): 
    if os.path.isabs(x): return x
    else: return os.path.join(filepath(),x)
    

Config = None
config_filelist = ['config.ini']
   
class ConfigDatabase(AutoConfigTemplate):
    """
    dbname=string:llampex
    dbuser=string:llampexuser
    dbpasswd=string:llampexpasswd
    dbhost=hostname:127.0.0.1
    dbport=int:5432
    createtables=bool:False
    """



def reloadConfig(saveTemplate = False):
    global Config, config_filelist
    fullpath_filelist = [ filedir(x) for x in config_filelist ]
    if not os.path.isfile(fullpath_filelist[0]):
        print "INFO: config.ini not found. Creating one for *you*."
        try:
            f_out = open(fullpath_filelist[0],"w")
            f_in = open(filedir("config.template.ini"),"r")
            f_out.write(f_in.read())
            f_out.close()
            f_in.close()
        except Exception, e:
            print "WARN: Some error ocurred, try to copy manually config.template.ini to config.ini"
            print repr(e)
            
        
    Config = ConfigReader(files=fullpath_filelist, saveConfig = saveTemplate)
    Config.Database = ConfigDatabase(Config,section = "database")
    
    if saveTemplate:
        f1w = open(saveTemplate, 'wb')
        Config.configini.write(f1w)
        f1w.close()
    else:
        if Config.errors:
            print "INFO: ** La configuracion esta desactualizada, ejecute <python config.py update > para actualizarla ** "
    return Config


def main():
    if len(sys.argv) > 1:
        if sys.argv[1] == 'savetemplate':
            global config_filelist 
            config_filelist = []
            reloadConfig(saveTemplate = 'config.template.ini')
        elif sys.argv[1] == 'update':
            reloadConfig(saveTemplate = 'config.ini')
    else:
        reloadConfig()
        print "host:", repr(Config.Database.host), type(Config.Database.host)
        print "port:", repr(Config.Database.port), type(Config.Database.port)


if __name__ == "__main__": main()
else: reloadConfig()