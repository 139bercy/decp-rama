from sqlalchemy import create_engine, Column, Integer, String, Numeric, Boolean, JSON, ForeignKey, Date, TIMESTAMP
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()

class Source(Base):
    __tablename__ = 'source'
    
    source_id = Column(Integer, primary_key=True)
    nom = Column(String(255), nullable=False, unique=True)
    alias = Column(String(255))
    dataset_id = Column(Integer, nullable=False)
    status = Column(String(50))
    actif = Column(Boolean, nullable=False, default=True)

