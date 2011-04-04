from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Table, Column, Integer, String, MetaData, ForeignKey, Boolean

from . import Base

class RowProject(Base):
    __tablename__ = 'projects'
    
    id = Column(Integer, primary_key=True)
    code = Column(String(64), nullable=False, unique=True)
    description = Column(String(255), nullable=False, default="")
    db = Column(String(64), nullable=False)
    path = Column(String(255), nullable=False)
    host = Column(String(64))
    port = Column(Integer)
    user = Column(String(64))
    password = Column(String(64))
    active = Column(Boolean, nullable=False, default=True)
    
    def __str__(self):
        return "<RowProject code=%s active=%s>" % (
            repr(self.code), 
            repr(self.active) 
            )