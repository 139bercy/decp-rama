from sqlalchemy import create_engine, Column, Integer, String, Numeric, Boolean, JSON, ForeignKey, Date, TIMESTAMP
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()

=
# Classe pour la connexion à la base de données
class DbConnect:
    def __init__(self, db_url):
        self.engine = create_engine(db_url)
        Base.metadata.create_all(self.engine)  # Crée les tables
        self.Session = sessionmaker(bind=self.engine)
    
    def get_session(self):
        return self.Session()

# Exemple d'utilisation (à ajuster avec votre URL de base de données)
if __name__ == "__main__":
    db_url = 'postgresql://user:password@localhost/mydatabase'  # Remplacez par vos informations de connexion
    db = DbConnect(db_url)

    # Utilisation d'une session
    with db.get_session() as session:
        # Exécuter votre logique ici
        pass
