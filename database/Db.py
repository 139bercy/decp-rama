import json
import psycopg2
from os import environ as env

import locale
import logging

logging.getLogger('db').propagate = False
logger = logging.getLogger(__name__)
locale.setlocale(locale.LC_ALL, 'fr_FR.UTF-8')

class Db:
    ERROR_MESSAGE_SESSION_BEGIN = "Une erreur s'est produite lors de la fermeture de la session"
    ERROR_MESSAGE_SESSION_END = "Une erreur s'est produite lors de la fermeture de la session"
    ERROR_MESSAGE_STEP = "Une erreur s'est produite lors de la recherche ou de l'ajout de l'étape :"
    ERROR_MESSAGE_SOURCE = "Une erreur s'est produite lors de la recherche ou de l'ajout de la source"
    ERROR_MESSAGE_FILE = "Une erreur s'est produite lors de la recherche ou de l'ajout du fichier :"
    ERROR_MESSAGE_EXCLUSION = "Une erreur s'est produite lors de la recherche ou de l'ajout du type d'exclusion :"
    ERROR_MESSAGE_SESSION_REPORT = "Une erreur s'est produite lors de la recherche ou de l'ajout d'un élément du rapport':"
    
    def __init__(self,filename='database.ini', section='postgresql'):
        # Load config file
        config_file = "config.json"
        with open(config_file, "r") as f:
            config = json.load(f)
            self.connection_params = {
                'dbname': env.get("postgresql.decp.database", config["database"]["dbname"]),  # Nom de la base de données
                'user': env.get("postgresql.decp.user", config["database"]["user"]),  # Nom de l'utilisateur
                'password': env.get("postgresql.decp.password", config["database"]["password"]),  # Mot de passe
                'host': env.get("postgresql.decp.host",  config["database"]["host"]),  # ou l'adresse de votre serveur
                'port': env.get("postgresql.decp.port",  config["database"]["port"])  # Port par défaut de PostgreSQL
            }

    def connect(self):
        """ Connect to the PostgreSQL database server """
        conn = None
        try:
            # connect to the PostgreSQL server
            logging.info('Connecting to the PostgreSQL database...')
            conn = psycopg2.connect(**self.connection_params)
            
            # create a cursor
            cur = conn.cursor()
            
        # execute a statement
            logging.info('PostgreSQL database version:')
            cur.execute('SELECT version()')

            # display the PostgreSQL database server version
            db_version = cur.fetchone()
            logging.info(db_version)
        
        # close the communication with the PostgreSQL
            cur.close()
        except (Exception, psycopg2.DatabaseError) as error:
            logging.error(error)
        finally:
            if conn is not None:
                conn.close()
                logging.info('Database connection closed.')

    def add_session(self,session_name):
        """
        Ajoute une entrée dans la table session.
        :return: report_session_id de l'étape
        """
        session_id = None
        try:
            # Connexion à la base de données
            connection = psycopg2.connect(**self.connection_params)
            cursor = connection.cursor()

            cursor.execute("INSERT INTO decp_report.session (session_id, name, begin_date) VALUES (nextval('decp_report.s_session'), %s, NOW()) RETURNING session_id", (session_name,))
            session_id = cursor.fetchone()[0]  # Récupère le nouveau step_id

            # Commit des changements
            connection.commit()

        except Exception as e:
            logging.error(self.ERROR_MESSAGE_SESSION_BEGIN, e)
        finally:
            # Fermeture de la connexion
            if cursor:
                cursor.close()
            if connection:
                connection.close()

        return session_id

    def end_session(self,session_id:int,message:str):
        """
        Ajoute la date de fin lénregistrement avec le session_id dans la table session.
        :return: session_id de l'étape
        """
        try:
            # Connexion à la base de données
            connection = psycopg2.connect(**self.connection_params)
            cursor = connection.cursor()

            cursor.execute("UPDATE decp_report.session SET message=%s, end_date = NOW() WHERE session_id = %s RETURNING session_id", (message,session_id,))
            session_id = cursor.fetchone()[0]  # Récupère le nouveau step_id

            # Commit des changements
            connection.commit()

        except Exception as e:
            logging.error(self.ERROR_MESSAGE_SESSION_END, e)
        finally:
            # Fermeture de la connexion
            if cursor:
                cursor.close()
            if connection:
                connection.close()

        return session_id

    def add_report(self, session_id:int, step_id:int, source_id:int, file_id:int, exclusion_type_id:int, message, error, path, position:int, id_content:str, content):
        """
        Ajoute un enregistrement dans la table decp.report
        :param session_id: INT8, identifiant de la session
        :param step_id: INT8, identifiant de l'étape
        :param source_id: INT8, identifiant de la source
        :param file_id: INT8, identifiant du fichier
        :param exclusion_type_id: INT8, identifiant du type d'exclusion
        :param message: VARCHAR(256), message
        :param error: VARCHAR(256), message d'erreur
        :param path: VARCHAR(256), Chemin de l'erreur
        :param position: VARCHAR(256), position
        :param id_content: VARCHAR(64), Identifiant de l'enregistrement exclu/invalide (extrait du contenu en erreur "content")
        :param content: BYTEA, contenu
        """
        try:
            # Connexion à la base de données
            connection_params = self.connection_params
            connection = psycopg2.connect(**connection_params)
            cursor = connection.cursor()

            # Instruction SQL pour insérer un enregistrement
            insert_query = """
                INSERT INTO decp_report.report (report_id, session_id, step_id, source_id, file_id, exclusion_type_id, message, error, path, position, id_content, content, creation_date)
                VALUES (nextval('decp_report.s_report'), %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
            """

            # Exécution de la requête d'insertion
            if len(str(content))>4096:
                content = str(content)[0:4090]+"..." 
            if len(str(error))>2048:
                error = str(error)[0:1020]+" (...) "+str(error)[len(str(error))-1020:len(str(error))] 
            cursor.execute(insert_query, (session_id, step_id, source_id, file_id, exclusion_type_id, message, error, path, position, id_content, str(content)))

            # Commit des changements
            connection.commit()

        except Exception as e:
            logging.error(self.ERROR_MESSAGE_SESSION_REPORT, e)
        finally:
            # Fermeture de la connexion
            if cursor:
                cursor.close()
            if connection:
                connection.close()


    def find_or_add_step(self, step_name):
        """
        Recherche un step par son nom et l'ajoute s'il n'existe pas.
        :param step_name: Nom de l'étape à rechercher
        :return: step_id de l'étape
        """
        step_id = None
        try:
            # Connexion à la base de données
            connection = psycopg2.connect(**self.connection_params)
            cursor = connection.cursor()

            # Vérification si l'étape existe déjà
            cursor.execute("SELECT step_id FROM decp_report.step WHERE name = %s", (step_name,))
            result = cursor.fetchone()

            if result:
                step_id = result[0]  # Récupère le step_id si trouvé
            else:
                # Si l'étape n'existe pas, l'ajouter
                cursor.execute("INSERT INTO decp_report.step (step_id, name, creation_date) VALUES (nextval('decp_report.s_step'), %s, NOW()) RETURNING step_id", (step_name,))
                step_id = cursor.fetchone()[0]  # Récupère le nouveau step_id

            # Commit des changements
            connection.commit()

        except Exception as e:
            logging.error(self.ERROR_MESSAGE_STEP, e)
        finally:
            # Fermeture de la connexion
            if cursor:
                cursor.close()
            if connection:
                connection.close()

        return step_id

    def find_or_add_file(self, file_name:str, source_id:int, nb_marches:int, nb_concessions:int):
        """
        Recherche un fichier par son nom et l'ajoute s'il n'existe pas.
        :param source_id: INT8, identifiant de la source
        :param nb: INT8, Nombre d'enregistrement dans la source
        """
        file_id = None
        try:
            connection = psycopg2.connect(**self.connection_params)
            cursor = connection.cursor()
            
            cursor.execute("SELECT file_id FROM decp_report.file WHERE name = %s", (file_name,))
            result = cursor.fetchone()

            if result:
                file_id = result[0]
            else:
                cursor.execute("INSERT INTO decp_report.file (file_id, name, source_id, nb_marches, nb_concessions, creation_date) VALUES (nextval('decp_report.s_file'), %s, %s, %s, %s, NOW()) RETURNING file_id", (file_name, source_id, nb_marches, nb_concessions))
                file_id = cursor.fetchone()[0]

            connection.commit()

        except Exception as e:
            logging.error(self.ERROR_MESSAGE_FILE, e)
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

        return file_id

    def find_or_add_exclusion_type(self, code):
        """ Recherche un type d'exclusion par son code ou nom et l'ajoute s'il n'existe pas. """
        exclusion_type_id = None
        try:
            connection = psycopg2.connect(**self.connection_params)
            cursor = connection.cursor()
            
            cursor.execute("SELECT exclusion_type_id FROM decp_report.exclusion_type WHERE code = %s", (code, ))
            result = cursor.fetchone()

            if result:
                exclusion_type_id = result[0]  # Récupère l'id si trouvé
            else:
                cursor.execute("INSERT INTO decp_report.exclusion_type (exclusion_type_id, code, name, creation_date) VALUES (nextval('decp_report.s_exclusion_type'), %s, %s, NOW()) RETURNING exclusion_type_id", (code, code))
                exclusion_type_id = cursor.fetchone()[0]  # Récupère le nouvel id

            connection.commit()

        except Exception as e:
            logging.error(self.ERROR_MESSAGE_EXCLUSION, e)
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

        return exclusion_type_id

    def find_or_add_source(self, source_name):
        """
        Recherche une source par son nom et l'ajoute si elle n'existe pas.
        :param connection_params: Dictionnaire des paramètres de connexion
        :param source_name: Nom de la source à rechercher
        :param creation_date: Date de création à associer à la nouvelle source
        :return: source_id de la source
        """
        source_id = None
        try:
            # Connexion à la base de données
            connection = psycopg2.connect(**self.connection_params)
            cursor = connection.cursor()

            # Vérification si la source existe déjà
            cursor.execute("SELECT source_id FROM decp_report.source WHERE name = %s", (source_name,))
            result = cursor.fetchone()

            if result:
                source_id = result[0]  # Récupère le source_id si trouvé
            else:
                # Si la source n'existe pas, l'ajouter
                cursor.execute("INSERT INTO decp_report.source (source_id, name, creation_date) VALUES (nextval('decp_report.s_source'), %s, NOW()) RETURNING source_id", (source_name,))
                source_id = cursor.fetchone()[0]  # Récupère le nouvel source_id

            # Commit des changements
            connection.commit()

        except Exception as e:
            logging.error(self.ERROR_MESSAGE_SOURCE, e)
        finally:
            # Fermeture de la connexion
            if cursor:
                cursor.close()
            if connection:
                connection.close()

        return source_id


if __name__ == '__main__':
    db = Db()
    db.connect()
