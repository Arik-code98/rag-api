from sqlalchemy import create_engine, Column, Integer, String, select
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL="sqlite:///./users.db"
engine=create_engine(DATABASE_URL, connect_args={"check_same_thread":False})
SessionLocal=sessionmaker(bind=engine)
Base=declarative_base()

class User(Base):
    __tablename__="users"
    id=Column(Integer,primary_key=True)
    username=Column(String,unique=True)
    hashed_password=Column(String)

Base.metadata.create_all(bind=engine)