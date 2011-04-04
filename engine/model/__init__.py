from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import MetaData

Base = declarative_base()
from table_projects import Project

metadata = Base.metadata
engine = None
session = None