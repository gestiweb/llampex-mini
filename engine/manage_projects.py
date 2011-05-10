# encoding: UTF-8
from bjsonrpc.exceptions import ServerError
from bjsonrpc.handlers import BaseHandler

import model
from model import RowProject, RowUser, RowProjectUser
from project_manager import compute_password


class ManageProjects(BaseHandler):
    def __init__(self, rpc):
        BaseHandler.__init__(self,rpc)

    ########### USERS ###########
    def getUsers(self):
        userslist = []
        query = model.session.query(RowUser).order_by(RowUser.id)
        for rowuser in query:
            userslist.append([rowuser.username,rowuser.active,rowuser.admin])
        return userslist
    
    def modifyUser(self, user_row):
        user = model.session.query(RowUser).filter(RowUser.username == user_row[3]).first()
        
        user.active = user_row[1]
        user.admin = user_row[2]
        if user_row[0] != user_row[3]:
            user.username = user_row[0]
            
        model.session.commit()
    
    def modifyUserPass(self, username, newPass):
        user = model.session.query(RowUser).filter(RowUser.username == username).first()
        user.password = compute_password(newPass)
        model.session.commit()
        
    def newUser(self, username, password, active, admin):
        user = RowUser()
        user.username = username
        user.password = compute_password(password)
        user.active = active
        user.admin = admin
            
        model.session.add(user)
        model.session.commit()
        
    def delUser(self, username):
        user = model.session.query(RowUser).filter(RowUser.username == username).first()
        
        #TODO implementate cascade
        query = model.session.query(RowProjectUser).filter(RowProjectUser.user == user)
        for row in query:
            model.session.delete(row)
            
        model.session.delete(user)
        model.session.commit()
        
    ########### PROJECTS ###########
    def getProjects(self):
        projectslist = []
        query = model.session.query(RowProject).order_by(RowProject.id)
        for rowproj in query:
            projectslist.append([rowproj.code,rowproj.description,rowproj.db,
                              rowproj.path,rowproj.host,rowproj.port,
                              rowproj.user,rowproj.active])
        return projectslist
    
    def modifyProject(self, proj_row):
        proj = model.session.query(RowProject).filter(RowProject.code == proj_row[8]).first()
                                   
        proj.description = proj_row[1]
        proj.db = proj_row[2]
        proj.path = proj_row[3]
        proj.host = None if (proj_row[4] == "") else proj_row[4]
        proj.port = None if (proj_row[5] == "") else proj_row[5]
        proj.user = None if (proj_row[6] == "") else proj_row[6]
        proj.active = proj_row[7]
        if proj_row[0] != proj_row[8]:
            proj.code = proj_row[0]
            
        model.session.commit()
        
    def modifyProjPass(self, code, newPass, encrypt):
        #TODO: Implementate encryption
        project = model.session.query(RowProject).filter(RowProject.code == code).first()
        if encrypt == "None":
            project.password = newPass
            project.passwdcipher = None
        model.session.commit()
        
    def newProject(self, code, desc, db, path, host, port, user, password, encrypt, active):
        project = RowProject()
        project.code = code
        project.description = desc
        project.db = db
        project.path = path
        project.host = None if (host == "") else host
        project.port = None if (port == "") else port
        project.user = None if (user == "") else user
        project.active = active
        
        #TODO: Implementate Encryption
        if encrypt == "None":
            project.password = None if (password == "") else password
            project.passwdcipher = None
            
        model.session.add(project)
        model.session.commit()
        
    def delProject(self, code):
        project = model.session.query(RowProject).filter(RowProject.code == code).first()
        
        #TODO implementate cascade
        query = model.session.query(RowProjectUser).filter(RowProjectUser.project == project)
        for row in query:
            model.session.delete(row)
        
        model.session.delete(project)
        model.session.commit()


    ########### USERS/PROJECTS ###########
    def getActiveUsers(self,project):
        userslist = []
        query = model.session.query(RowUser).filter(
            RowUser.id.in_(model.session.query(RowProjectUser.user_id).filter(
            RowProjectUser.project_id.in_(model.session.query(RowProject.id).filter(RowProject.code == project)))))
        for row in query:
            userslist.append(row.username)
        return userslist
    
    def getInactiveUsers(self,project):
        userslist = []
        query = model.session.query(RowUser).filter(
            ~RowUser.id.in_(model.session.query(RowProjectUser.user_id).filter(
            RowProjectUser.project_id.in_(model.session.query(RowProject.id).filter(RowProject.code == project)))))
        for row in query:
            userslist.append(row.username)
        return userslist
    
    def addUserToProject(self,user,project):
        userProj = RowProjectUser()
        userProj.project = model.session.query(RowProject).filter(RowProject.code == project).one()
        userProj.user = model.session.query(RowUser).filter(RowUser.username == user).one()
        model.session.add(userProj)
        model.session.commit()
    
    def delUserFromProject(self,user,project):
        usr = model.session.query(RowUser).filter(RowUser.username == user).one()
        proj = model.session.query(RowProject).filter(RowProject.code == project).one()
        userProj = model.session.query(RowProjectUser).filter(RowProjectUser.user == usr).filter(RowProjectUser.project == proj).one()
        model.session.delete(userProj)
        model.session.commit()
        
        
def getManageProjects(rpc):
    manageProjects = ManageProjects(rpc)
    return manageProjects