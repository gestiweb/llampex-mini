import model # import Project, metadata, engine, session
from model import RowUser, RowProject, RowProjectUser    
from project_manager import compute_password
from getpass import getpass

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
            'dbname' : "llampex",
            'dbuser' : "llampexuser",
            'dbpasswd' : "llampexpasswd",
            'dbhost' : "127.0.0.1",
            'dbport' : 5432
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

def do_lsproject():
    print "Project List:"
    for p in model.session.query(RowProject):
        print "-", p.code,":", p

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
        print "No user found with that name. Giving up."
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
        project1.path = os.apth.realpath(filedir("../"))
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
        print "     addproject - adds a project to llampex."
        print "     lsuser - shows the userlist."
        print "     lsproject - shows the project list."
        print "     passwd - update a user password"
        print "     addprojectuser - grants acces to a project for a user"
        print "     delprojectuser - revokes access to a project for a user"
        

if __name__ == "__main__":
    main()
    

    
    
        
        
    