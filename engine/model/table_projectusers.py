from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Table, Column, Integer, String, MetaData, ForeignKey, Boolean
from sqlalchemy.orm import relationship, backref

from . import Base

class RowProjectUser(Base):
    __tablename__ = 'projectusers'
    
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey('projects.id'))
    project = relationship("RowProject", backref=backref('users', order_by=id))    

    user_id = Column(Integer, ForeignKey('users.id'))
    user = relationship("RowUser", backref=backref('projects', order_by=id))    

    def __str__(self):
        return "<RowProjectUser(%s) projectcode=%s username=%s>" % (
            repr(self.id),
            repr(self.project.code), 
            repr(self.user.username) 
            )