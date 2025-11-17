import locale
import logging
import os
import psycopg2
from psycopg2 import sql
from os import environ as env
from dotenv import load_dotenv

logging.getLogger('db').propagate = False
logger = logging.getLogger(__name__)
locale.setlocale(locale.LC_ALL, 'fr_FR.UTF-8')

class DbDecp:
    ERROR_MESSAGE_SOURCE = "Une erreur s'est produite lors de la recherche ou de l'ajout de la source"
    ERROR_MESSAGE_FILE = "Une erreur s'est produite lors de la recherche ou de l'ajout du fichier :"
 
    def __init__(self):
        # Chargement des variables d'environnement depuis le fichier .env
        load_dotenv()

        self.connection = psycopg2.connect(
            dbname=os.getenv('DECP.DB_NAME'),
            user=os.getenv('DECP.DB_USER'),
            password=os.getenv('DECP.DB_PASSWORD'),
            host=os.getenv('DECP.DB_HOST', 'localhost'),
            port=os.getenv('DECP.DB_PORT', '5432')
        )

        self.cursor = self.connection.cursor()

    def find_or_add_source(self, source_name:str, dataset_id:str):
        """
        Recherche un fichier par son nom et l'ajoute s'il n'existe pas.
        :param source_id: INT8, identifiant de la source
        :param nb: INT8, Nombre d'enregistrement dans la source
        """
        source_id = None
        try:
            cursor = self.cursor
            
            cursor.execute("SELECT source_id FROM public.source WHERE nom = %s", (source_name,))
            result = cursor.fetchone()

            if result:
                source_id = result[0]
            else:
                cursor.execute("INSERT INTO public.source (source_id, nom, dataset_id, date_creation) VALUES (nextval('public.s_source'), %s, %s, NOW()) RETURNING source_id", (source_name,dataset_id))
                source_id = cursor.fetchone()[0]

            self.commit()

        except Exception as e:
            logging.error(self.ERROR_MESSAGE_SOURCE, e)
        finally:
            # Fermeture systématique du curseur après utilisation
            self.cursor.close()

        return source_id

    def find_or_add_file(self, file_name:str, source_id:int, nb_marches, nb_concessions):
        """
        Recherche un fichier par son nom et l'ajoute s'il n'existe pas.
        :param source_id: INT8, identifiant de la source
        :param nb: INT8, Nombre d'enregistrement dans la source
        """
        file_id = None
        try:
            cursor = self.cursor
            
            cursor.execute("SELECT file_id FROM public.file WHERE name = %s", (file_name,))
            result = cursor.fetchone()

            if result:
                file_id = result[0]
            else:
                cursor.execute("INSERT INTO public.file (file_id, name, source_id, nb_marches, nb_concessions, creation_date) VALUES (nextval('public.s_file'), %s, %s, %s, %s, NOW()) RETURNING file_id", (file_name, source_id, nb_marches, nb_concessions))
                file_id = cursor.fetchone()[0]

            self.commit()

        except Exception as e:
            logging.error(self.ERROR_MESSAGE_FILE, e)
        finally:
            # Fermeture systématique du curseur après utilisation
            self.cursor.close()

        return file_id

    def add_marche(self, id, acheteur, titulaires, date_notification, montant, json_data):
        try:
            # Démarrer une transaction
            self.cursor.execute("BEGIN;")

            # Définir les valeurs à insérer
            new_values = (id, acheteur, titulaires, date_notification, montant, json_data)

            # Déplacer l'ancien enregistrement si existant
            self.cursor.execute("""
                INSERT INTO ancien_marche (id, acheteur, titulaires, dateNotification, montant, json)
                SELECT m.id, m.acheteur, m.titulaires, m.dateNotification, m.montant, m.json
                FROM marche m
                WHERE (m.id = %s AND m.acheteur = %s AND m.titulaires = %s AND m.dateNotification = %s AND m.montant = %s)
            """, new_values)

            # Insérer le nouvel enregistrement
            self.cursor.execute("""
                INSERT INTO marche (id, acheteur, titulaires, dateNotification, montant, json)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (id, acheteur, titulaires, dateNotification, montant) 
                DO NOTHING;
            """, new_values)

            # Valider la transaction
            self.connection.commit()

        except Exception as e:
            print(f"Erreur lors de l'ajout du marché: {e}")
            # Annuler la transaction en cas d'erreur
            self.connection.rollback()

        finally:
            # Fermeture systématique du curseur après utilisation
            self.cursor.close()

    def close(self):
        self.connection.close()
