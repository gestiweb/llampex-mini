# coding: UTF8
from autoconfig.autoconfig import AutoConfigTemplate, ConfigReader
import sys

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
    Config = ConfigReader(files=config_filelist, saveConfig = saveTemplate)
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