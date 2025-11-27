from sqlalchemy import create_engine, Column, Integer, String, Numeric, Boolean, JSON, ForeignKey, Date, TIMESTAMP
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()

class Marche(Base):
    __tablename__ = 'marche'
    
    data_id = Column(Integer, primary_key=True)
    source_id = Column(Integer, ForeignKey('source.source_id'), nullable=False)
    file_id = Column(Integer, ForeignKey('file.file_id'), nullable=False)
    acheteur = Column(String(255), nullable=False)
    titulaire = Column(String(255), nullable=False)
    date_notification = Column(Date, nullable=False)
    montant = Column(Numeric, nullable=False)
    data = Column(JSON, nullable=False)
    
    __table_args__ = (
        UniqueConstraint('acheteur', 'titulaire', 'date_notification', 'montant', name='uq_marche'),
    )
