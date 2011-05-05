# encoding: UTF-8
from bjsonrpc.exceptions import ServerError
from bjsonrpc.handlers import BaseHandler

import model
from model import RowProject, RowUser, RowProjectUser
from project_manager import compute_password


class ManageProjects(BaseHandler):
    def __init__(self, rpc):
        BaseHandler.__init__(self,rpc)
    
    def getUsers(self):
        userslist = []
        query = model.session.query(RowUser)
        for rowuser in query:
            userslist.append({'username':rowuser.username,'active':rowuser.active})
        return userslist
    
    def modifyUser(self, user_row):
        user = model.session.query(RowUser).filter(RowUser.username == user_row[2]).first()
        
        user.active = user_row[1]
        if user_row[0] != user_row[2]:
            user.username = user_row[0]
            
        model.session.commit()
    
    def modifyUserPass(self, username, newPass):
        user = model.session.query(RowUser).filter(RowUser.username == username).first()
        user.password = compute_password(newPass)
        model.session.commit()
        
    def newUser(self, username, password, active):
        user = RowUser()
        user.username = username
        user.password = compute_password(password)
        user.active = active
            
        model.session.add(user)
        model.session.commit()
        
    def delUser(self, username):
        user = model.session.query(RowUser).filter(RowUser.username == username).first()
        model.session.delete(user)
        model.session.commit()
        
        
def getManageProjects(rpc):
    manageProjects = ManageProjects(rpc)
    return manageProjects