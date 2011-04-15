from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Table, Column, Integer, String, MetaData, ForeignKey, Boolean
from sqlalchemy.orm import relation as relationship

from . import Base


class RowUser(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(64), nullable=False, unique=True)
    password = Column(String(255))
    active = Column(Boolean, nullable=False, default=True)
    
    def __str__(self):
        return "<RowUser(%s) username=%s active=%s>" % (
            repr(self.id),
            repr(self.username), 
            repr(self.active) 
            )