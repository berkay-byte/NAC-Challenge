# api/models.py

from sqlalchemy import Column, Integer, String, DateTime, BigInteger
from database import Base
import datetime

class RadCheck(Base):
    __tablename__ = "radcheck"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(64), index=True, nullable=False)
    attribute = Column(String(64), nullable=False)
    op = Column(String(2), nullable=False)
    value = Column(String(253), nullable=False)

class RadReply(Base):
    __tablename__ = "radreply"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(64), index=True, nullable=False)
    attribute = Column(String(64), nullable=False)
    op = Column(String(2), nullable=False, default="=")
    value = Column(String(253), nullable=False)

class RadUserGroup(Base):
    __tablename__ = "radusergroup"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(64), index=True, nullable=False)
    groupname = Column(String(64), nullable=False)
    priority = Column(Integer, nullable=False, default=1)

class RadGroupReply(Base):
    __tablename__ = "radgroupreply"
    id = Column(Integer, primary_key=True, index=True)
    groupname = Column(String(64), index=True, nullable=False)
    attribute = Column(String(64), nullable=False)
    op = Column(String(2), nullable=False, default="=")
    value = Column(String(253), nullable=False)

class RadAcct(Base):
    __tablename__ = "radacct"
    radacctid = Column(BigInteger, primary_key=True, index=True)
    acctsessionid = Column(String(64), index=True, nullable=False)
    username = Column(String(64), index=True)
    nasipaddress = Column(String(15), nullable=False)
    acctstarttime = Column(DateTime, default=datetime.datetime.utcnow)
    acctupdatetime = Column(DateTime)
    acctstoptime = Column(DateTime)
    acctsessiontime = Column(Integer)
    acctinputoctets = Column(BigInteger) 
    acctoutputoctets = Column(BigInteger)
    framedipaddress = Column(String(15))
    acctterminatecause = Column(String(32))
    