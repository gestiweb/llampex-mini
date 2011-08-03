from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import MetaData

Base = declarative_base()
from table_projects import RowProject
from table_users import RowUser
from table_projectusers import RowProjectUser
from table_userconfigs import RowUserConfig

metadata = Base.metadata
engine = None
session = None