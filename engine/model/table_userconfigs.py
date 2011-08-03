from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Table, Column, Integer, String, MetaData, ForeignKey, Boolean
from sqlalchemy.orm import relation as relationship
from sqlalchemy.orm import backref

from . import Base

class RowUserConfig(Base):
    __tablename__ = 'userconfigs'
    
    id = Column(Integer, primary_key=True)
    user = Column(String(64))
    project = Column(String(64))
    configname = Column(String(128))
    value = Column(String)

    def __str__(self):
        return "<RowUserConfig(%s) projectcode=%s username=%s configname=%s>" % (
            repr(self.id),
            repr(self.project), 
            repr(self.user),
            repr(self.configname)
            )
