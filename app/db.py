import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base,sessionmaker
load_dotenv(); url=os.getenv("DATABASE_URL","sqlite:///./sin_nombre.db")
if url.startswith("postgres://"): url=url.replace("postgres://","postgresql+psycopg://",1)
elif url.startswith("postgresql://"): url=url.replace("postgresql://","postgresql+psycopg://",1)
kw={"connect_args":{"check_same_thread":False}} if url.startswith("sqlite") else {"pool_pre_ping":True}
engine=create_engine(url,**kw); SessionLocal=sessionmaker(bind=engine,autoflush=False,autocommit=False); Base=declarative_base()
def get_db():
 d=SessionLocal()
 try: yield d
 finally: d.close()
