from sqlalchemy import create_engine, Column, Integer, String, Numeric, Boolean, JSON, ForeignKey, Date, TIMESTAMP
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()

class Concession(Base):
    __tablename__ = 'concession'
    
    concession_id = Column(Integer, primary_key=True)
    source_id = Column(Integer, ForeignKey('source.source_id'), nullable=False)
    file_id = Column(Integer, ForeignKey('file.file_id'), nullable=False)
    autorite_concedante = Column(String(255), nullable=False)
    concessionnaires = Column(String(255), nullable=False)
    date_debut_execution = Column(Date, nullable=False)
    valeur_globale = Column(Numeric, nullable=False)
    data = Column(JSON, nullable=False)
    
    __table_args__ = (
        UniqueConstraint('autorite_concedante', 'concessionnaires', 'date_debut_execution', 'valeur_globale', name='uq_concession'),
    )
