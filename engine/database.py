import model # import Project, metadata, engine, session
from model import RowUser, RowProject, RowProjectUser    
from project_manager import compute_password
from getpass import getpass
from config import Config
import os.path
import yaml 

def connect(dboptions, echo = True):
    from sqlalchemy import create_engine
    conn_url = 'postgresql://%(dbuser)s:%(dbpasswd)s@%(dbhost)s:%(dbport)d/%(dbname)s' % dboptions
    #print conn_url
    model.engine = create_engine(conn_url, echo=echo)
    model.Base.metadata.bind = model.engine
    from sqlalchemy.orm import sessionmaker
    Session = sessionmaker(bind=model.engine)
    # create a Session
    model.session = Session()

def filepath(): return os.path.abspath(os.path.dirname(__file__))

def filedir(x): # convierte una ruta relativa a este fichero en absoluta
    if os.path.isabs(x): return x
    else: return os.path.join(filepath(),x)


def main():
    dboptions = {
            'dbname' : Config.Database.dbname,
            'dbuser' : Config.Database.dbuser,
            'dbpasswd' : Config.Database.dbpasswd,
            'dbhost' : Config.Database.dbhost,
            'dbport' : Config.Database.dbport
            }
    connect(dboptions, echo = False)
    import sys
    
    params = []
    if len(sys.argv) < 2: cmd = "help"
    else:
        cmd = sys.argv[1]
        params = sys.argv[2:]
        
    if cmd == "help": do_help(*params)
    elif cmd == "init": do_init(*params)
    elif cmd == "lsuser": do_lsuser(*params)
    elif cmd == "lsproject": do_lsproject(*params)
    elif cmd == "adduser": do_adduser(*params)
    elif cmd == "deluser": do_deluser(*params)
    elif cmd == "addproject": do_addproject(*params)
    elif cmd == "delproject": do_delproject(*params)
    elif cmd == "passwd": do_passwd(*params)
    elif cmd == "addprojectuser": do_addprojectuser(*params)
    elif cmd == "delprojectuser": do_delprojectuser(*params)
    else: print "Unknown command or not implemented:", cmd

def do_adduser(username = None, password = None):
    if username is None:
        username = raw_input("Please give an username: ")
    if not username: return
    if password is None: 
        print "No password given, placing the same username as password."
        password = username
    user1 = RowUser()
    user1.username = username
    user1.password = compute_password(password)
    model.session.add(user1)
    model.session.commit()
    print "Username %s added. To change the password use 'passwd' command" % (
        repr(user1.username))
    
def do_deluser(username = None):
    if username is None:
        username = raw_input("Please give an username: ")
    if not username: return
    user1 = model.session.query(RowUser).filter(RowUser.username == username).first()
    if user1 is None:
        print "No user found with that name. Giving up."
        return
    verify = raw_input("Are you sure you want to delete the user "+repr(user1.username)+"? [Yes|No]: ")
    if verify != "Yes":
        print "Giving up."
        return
    model.session.delete(user1) #TODO deberia eliminarse en cascada
    model.session.commit()
    print "Username %s deleted." % (repr(user1.username))

def do_passwd(username = None, newpassword = None):
    if username is None:
        username = raw_input("Please give an username: ")
    if not username: return
    user1 = model.session.query(RowUser).filter(RowUser.username == username).first()
    if user1 is None:
        print "No user found with that name. Giving up."
        return
    if newpassword is None:
        newpassword = getpass()
        
    user1.password = compute_password(newpassword)
    model.session.commit()
    print "Password changed."

def do_lsproject(project = None):
    if project is None: # list projects
        print "Project List:"
        for p in model.session.query(RowProject):
            print "-", p.code,":", p
    else:
        project1 = model.session.query(RowProject).filter(RowProject.code == project).first()
        if project1 is None:
            print "No project found with that name. Giving up."
            return        
        for k in "id,code,description,db,path,host,port,user,password,active".split(","):
            print "- %s:" % k, repr(getattr(project1,k,None))
        print
          
def do_lsuser():
    print "User List:"
    for u in model.session.query(RowUser):
        print "-", u
    
def do_addprojectuser(username = None, project = None):
    if username is None:
        username = raw_input("Please give an username: ")
    if not username: return
    user1 = model.session.query(RowUser).filter(RowUser.username == username).first()
    if user1 is None:
        print "No user found with that name. Giving up."
        return
    if project is None:
        do_lsproject()
        project = raw_input("Give a project code: ")
    if not project: return
    project1 = model.session.query(RowProject).filter(RowProject.code == project).first()
    if project1 is None:
        print "No project found with that name. Giving up."
        return        
    projectuser1 = model.session.query(RowProjectUser).filter(RowProjectUser.user == user1).filter(RowProjectUser.project == project1).first()
    if projectuser1 is not None:
        print "User is already granted on that project."
        return
    projectuser1 = RowProjectUser()
    projectuser1.project = project1
    projectuser1.user = user1
    model.session.add(projectuser1)
    model.session.commit()
    print "User %s added to the project %s" % (username,project)
    
def do_delprojectuser(username = None, project = None):
    if username is None:
        username = raw_input("Please give an username: ")
    if not username: return
    user1 = model.session.query(RowUser).filter(RowUser.username == username).first()
    if user1 is None:
        print "No user found with that name. Giving up."
        return
    
    if project is None:
        do_lsproject()
        project = raw_input("Give a project code: ")
    if not project: return
    project1 = model.session.query(RowProject).filter(RowProject.code == project).first()
    if project1 is None:
        print "No project found with that name. Giving up."
        return
    
    userproject1 = model.session.query(RowProjectUser).filter(RowProjectUser.project_id == project1.id).filter(RowProjectUser.user_id == user1.id).first()
    
    if userproject1 is None:
        print "No user and project relation found with that name. Giving up."
        return
    
    verify = raw_input("Are you sure you want to delete this user-project relation? [Yes|No]: ")
    if verify != "Yes":
        print "Giving up."
        return
    model.session.delete(userproject1)
    model.session.commit()
    print "User-project relation deleted."
    
    
def do_addproject(code = None, description = None, db = None, path = None, host = None, port = None, user = None, password = None, active = None):
    if code is None:
        code = raw_input("Please give a code: ")
    if not code: return
    if model.session.query(RowProject).filter(RowProject.code == code).first():
        print "This project already exists. Giving up."
        return
    if description is None:
        description = raw_input("Please give a description: ")
    if db is None:
        db = raw_input("Please give a database: ")
    if not db: return
    if path is None:
        path = raw_input("Please give a path: ")
    if not path: return
    if host is None:
        host = raw_input("Please give a host: ")
    if not host: host = "127.0.0.1" # default is localhost
    if port is None:
        port = raw_input("Please give a port: ")
    if not port: port = "5432" # default is 5432
    if user is None:
        user = raw_input("Please give a user: ")
    if not user: user = "llampexuser" # default
    if password is None:
        password = raw_input("Please give a password: ")
    if not password: password = "llampexpasswd" # default
    if active is None:
        active = raw_input("Project is actived? [True|False]: ")
    if active != "False":
        active = "True" # default is true
        
    project1 = RowProject()
    project1.code = code
    project1.description = description
    project1.db = db
    project1.path = path
    project1.host = host
    project1.port = port
    project1.user = user
    project1.password = password
    project1.active = active
    
    model.session.add(project1)
    model.session.commit()
    print "Project %s added." % (repr(project1.code))
    
def do_delproject(code = None):
    if code is None:
        code = raw_input("Please give a code: ")
    if not code: return
    project1 = model.session.query(RowProject).filter(RowProject.code == code).first()
    if project1 is None:
        print "No project found with that name. Giving up."
        return
    verify = raw_input("Are you sure you want to delete the project "+repr(project1.code)+"? [Yes|No]: ")
    if verify != "Yes":
        print "Giving up."
        return
    model.session.delete(project1) #TODO deberia eliminarse en cascada
    model.session.commit()
    print "Project %s deleted." % (repr(project1.code))


def create_all():
    model.Base.metadata.create_all()

def do_init():
    create_all()
    project1 = model.session.query(RowProject).first()
    if project1 is None:
        print "No projects found. Creating a 'llampex' project"
        project1 = RowProject()
        project1.code = "llampex"
        project1.description = "Llampex main project"
        project1.db = "llampex"
        project1.path = os.path.realpath(filedir("../"))
        project1.active = True
        model.session.add(project1)
        model.session.commit()
        
    user1 = model.session.query(RowUser).first()
    if user1 is None:
        print "No users found. Creating a 'llampex' user with password 'llampex'"
        user1 = RowUser()
        user1.username = "llampex"
        user1.password = compute_password("llampex")
        model.session.add(user1)
        model.session.commit()
        for project in model.session.query(RowProject):
            nn = RowProjectUser()
            nn.user = user1
            nn.project = project
            model.session.add(nn)
            
            user1.projects.append(nn)
        model.session.commit()


def do_help():
        print "python database.py (command)" 
        print "Commands:"
        print "     help - prints this same help."
        print "     init - creates new tables and inits new rows."
        print "     adduser - adds a user to llampex."
        print "     deluser - delete a llampex user."
        print "     addproject - adds a project to llampex."
        print "     delproject - delete a llampex project."
        print "     lsuser - shows the userlist."
        print "     lsproject - shows the project list."
        print "     passwd - update a user password"
        print "     addprojectuser - grants acces to a project for a user"
        print "     delprojectuser - revokes access to a project for a user"
        

if __name__ == "__main__":
    main()
    

    
    
        
        
    