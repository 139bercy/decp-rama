from sqlalchemy import create_engine, Column, Integer, String, Numeric, Boolean, JSON, ForeignKey, Date, TIMESTAMP
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()

class File(Base):
    __tablename__ = 'file'
    
    file_id = Column(Integer, primary_key=True)
    source_id = Column(Integer, ForeignKey('source.source_id'), nullable=False)
    nom = Column(String(255), nullable=False)
    date_creation = Column(TIMESTAMP, nullable=False)
    
    __table_args__ = (
        UniqueConstraint('source_id', 'nom', name='uq_source_id_nom'),
    )
