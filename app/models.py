import uuid
from datetime import datetime
from sqlalchemy import String,Text,DateTime,ForeignKey,Integer
from sqlalchemy.orm import Mapped,mapped_column,relationship
from .db import Base
def now(): return datetime.utcnow()
class Thread(Base):
 __tablename__="threads"
 id:Mapped[str]=mapped_column(String(36),primary_key=True,default=lambda:str(uuid.uuid4()))
 title:Mapped[str]=mapped_column(String(120)); body:Mapped[str]=mapped_column(Text,default=""); image:Mapped[str|None]=mapped_column(String(200),nullable=True)
 author_hash:Mapped[str]=mapped_column(String(64)); created_at:Mapped[datetime]=mapped_column(DateTime,default=now); expires_at:Mapped[datetime]=mapped_column(DateTime,index=True)
 replies:Mapped[list["Reply"]]=relationship(back_populates="thread",cascade="all, delete-orphan")
class Reply(Base):
 __tablename__="replies"
 id:Mapped[str]=mapped_column(String(36),primary_key=True,default=lambda:str(uuid.uuid4()))
 thread_id:Mapped[str]=mapped_column(ForeignKey("threads.id",ondelete="CASCADE"),index=True)
 body:Mapped[str]=mapped_column(Text,default=""); image:Mapped[str|None]=mapped_column(String(200),nullable=True); alias_code:Mapped[str]=mapped_column(String(64))
 created_at:Mapped[datetime]=mapped_column(DateTime,default=now); thread:Mapped[Thread]=relationship(back_populates="replies")
