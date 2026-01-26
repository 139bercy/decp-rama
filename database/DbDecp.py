import json
import locale
import logging
import os
import psycopg2
import pandas as pd
from datetime import date
from dotenv import load_dotenv
from psycopg2 import sql
from psycopg2.extras import execute_values, Json
from os import environ as env

from utils.UtilsJson import UtilsJson

logging.getLogger('db').propagate = False
logger = logging.getLogger(__name__)
locale.setlocale(locale.LC_ALL, 'fr_FR.UTF-8')

# Classe d'accès à la base de données
# Défini la logique de dédoublonnage des données et l' ajout des enregistrements de marché et de concession 
class DbDecp:
    # Medsages d' erreur
    ERROR_MESSAGE_SESSION_BEGIN = "Une erreur s'est produite lors de la fermeture de la session"
    ERROR_MESSAGE_SESSION_END = "Une erreur s'est produite lors de la fermeture de la session"
    ERROR_MESSAGE_MARCHE = "Une erreur s'est produite lors de l' ajout du marché en base"
    ERROR_MESSAGE_CONCESSION = "Une erreur s'est produite lors de l' ajout de la concession en base"
    ERROR_MESSAGE_SOURCE = "Une erreur s'est produite lors de la recherche ou de l'ajout de la source"
    ERROR_MESSAGE_FILE = "Une erreur s'est produite lors de la recherche ou de l'ajout du fichier :"
 
    # Constructeur
    def __init__(self):
        # Chargement des variables d'environnement depuis le fichier .env
        load_dotenv()

        # Open database connection
        self.connection = psycopg2.connect(
            dbname=os.getenv('DECP.DB_NAME'),
            user=os.getenv('DECP.DB_USER'),
            password=os.getenv('DECP.DB_PASSWORD'),
            host=os.getenv('DECP.DB_HOST', 'localhost'),
            port=os.getenv('DECP.DB_PORT', '5432')
        )

    # Gestion des sessions

    def add_session(self,session_name:str):
        """
        Ajoute une entrée dans la table session.
        :return: session_id de l'exécution applicative en cours
        """
        session_id = None
        try:
            # Connexion à la base de données
            cursor = self.connection.cursor()

            # Insertion du nouvel enregistrement de la session
            cursor.execute("INSERT INTO decp.session (session_id, name, begin_date) VALUES (nextval('decp.s_session'), %s, NOW()) RETURNING session_id", (session_name,))
            session_id = cursor.fetchone()[0]  # Récupère le nouveau step_id

            # Commit des changements
            self.connection.commit()

        except Exception as e:
            logging.error(self.ERROR_MESSAGE_SESSION_BEGIN, e)
        finally:
            # Fermeture de la connexion
            if cursor:
                cursor.close()
            
        return session_id

    def end_session(self,session_id:int,message:str):
        """
        Ajoute la date de fin à l' enregistrement de la session (par son session_id) dans la table session.
        :return: session_id de l'étape
        """
        try:
            # Connexion à la base de données
            cursor = self.connection.cursor()

            cursor.execute("UPDATE decp.session SET message=%s, end_date = NOW() WHERE session_id = %s RETURNING session_id", (message,session_id,))
            session_id = cursor.fetchone()[0]  # Récupère le nouveau step_id

            # Commit des changements
            self.connection.commit()

        except Exception as e:
            logging.error(self.ERROR_MESSAGE_SESSION_END, e)
        finally:
            # Fermeture de la connexion
            if cursor:
                cursor.close()
            
        return session_id

    # Gestion des sources et fichiers sources

    def find_or_add_source(self, source_name:str, dataset_id:str):
        """
        Recherche une source par son nom et l'ajoute si elle n'existe pas.
        :param source_id: INT8, identifiant de la source
        :param nb: INT8, Nombre d'enregistrement dans la source
        :return: source_id id de l'enregistrement trouvé ou ajouté
        """
        source_id = None
        try:
            cursor = self.connection.cursor()
            
            cursor.execute("SELECT source_id FROM decp.source WHERE nom = %s", (source_name,))
            result = cursor.fetchone()

            if result:
                source_id = result[0]
            else:
                cursor.execute("INSERT INTO decp.source (source_id, nom, dataset_id, date_creation) VALUES (nextval('decp.s_source'), %s, %s, NOW()) RETURNING source_id", (source_name,dataset_id))
                source_id = cursor.fetchone()[0]

            self.connection.commit()

        except Exception as e:
            logging.error(self.ERROR_MESSAGE_SOURCE, e)
        finally:
            # Fermeture systématique du curseur après utilisation
            cursor.close()

        return source_id

    def find_or_add_file(self, file_name:str, source_id:int, nb_marches, nb_concessions):
        """
        Recherche un fichier par son nom et sa source puis l'ajoute s'il n'existe pas.
        :param source_id: INT8, identifiant de la source
        :param nb: INT8, Nombre d'enregistrement dans la source
        :return: file_id id de l'enregistrement trouvé ou ajouté
        """
        file_id = None
        try:
            cursor = self.connection.cursor()
            
            cursor.execute("SELECT file_id FROM decp.file WHERE nom = %s and source_id = %s", (file_name,source_id,))
            result = cursor.fetchone()

            if result:
                file_id = result[0]
            else:
                cursor.execute("INSERT INTO decp.file (file_id, nom, source_id, nb_marches, nb_concessions, date_creation) VALUES (nextval('decp.s_file'), %s, %s, %s, %s, NOW()) RETURNING file_id", (file_name, source_id, nb_marches, nb_concessions))
                file_id = cursor.fetchone()[0]

            self.connection.commit()

        except Exception as e:
            logging.error(self.ERROR_MESSAGE_FILE, e)
        finally:
            # Fermeture systématique du curseur après utilisation
            cursor.close()

        return file_id

    # Gestion des marchés

    def add_marche(self, source_id, file_id, file_date, index, id, acheteur, titulaires, date_notification, montant, objet, max_date, json_data):
        """
        Ajoute un marché si celui-ci n'existe pas déjà
        ou remplace un marché si celui-ci est retrouvé dans la table marché avec une date de
        publication maximale (modifications,acteSousTraitqnceModification) antérieure à celle du marché en entrée
        :return: marche_id l'id de l'enregistrement ajouté
        """
        marche_id = None
        try:
            cursor = self.connection.cursor()

            # Démarrer une transaction
            cursor.execute("BEGIN;")

            cursor.execute("""
                SELECT m.marche_id, m.max_date
                FROM decp.marche m
                WHERE (m.id = %s AND m.acheteur = %s AND m.titulaires = %s AND m.date_notification = %s AND m.montant = %s)
            """, (id, acheteur, titulaires, date_notification, montant,))
            result = cursor.fetchone()

            if result:
                found_marche_id = result[0]
                found_max_date = result[1]
                # reprise globale >= si la date es la même on considère que le premier ibséré (cad le dernier en date de fichier) edt le bln, le reste est en doublon
                # au jour le jour >
                if found_max_date is not None and file_date<found_max_date:
                    # Insérer le nouvel enregistrement directement dans les doublons
                    cursor.execute("""
                        INSERT INTO decp.marche_doublon (marche_doublon_id, source_id, file_id, indx, id, acheteur, titulaires, date_notification, montant, objet, max_date, date_creation, data_in)
                        VALUES (nextval('decp.s_marche_doublon'), %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        RETURNING marche_id;
                    """, (source_id, file_id, index, id, acheteur, titulaires, date_notification, montant, objet, max_date, file_date, json.dumps(json_data)))
                    marche_id = 0

                else:
                    # Déplacer l'enregistrement existant en doublon pour le remplacer
                    cursor.execute("""
                        INSERT INTO decp.marche_doublon (marche_doublon_id, marche_id, source_id, file_id, indx, id, acheteur, titulaires, date_notification, montant, objet, max_date, date_creation, data_in, data_out, data_augmente, est_retenu)
                        SELECT nextval('decp.s_marche_doublon'), m.marche_id, m.source_id, m.file_id, m.indx, m.id, m.acheteur, m.titulaires, m.date_notification, m.montant, m.objet, m.max_date, m.date_creation, m.data_in, m.data_out, m.data_augmente, m.est_retenu
                        FROM decp.marche m
                        WHERE (m.id = %s AND m.acheteur = %s AND m.titulaires = %s AND m.date_notification = %s AND m.montant = %s)
                    """, (id, acheteur, titulaires, date_notification, montant,))

                    # Suppression du doublon
                    cursor.execute("""
                        DELETE FROM decp.marche m
                        WHERE m.id = %s AND m.acheteur = %s AND m.titulaires = %s AND m.date_notification = %s AND m.montant = %s
                    """, (id, acheteur, titulaires, date_notification, montant,))

                    # Insérer le nouvel enregistrement
                    cursor.execute("""
                        INSERT INTO decp.marche (marche_id, source_id, file_id, indx, id, acheteur, titulaires, date_notification, montant, objet, max_date, date_creation, data_in)
                        VALUES (nextval('decp.s_marche'), %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (id, acheteur, titulaires, date_notification, montant) 
                        DO NOTHING
                        RETURNING marche_id;
                    """, (source_id, file_id, index, id, acheteur, titulaires, date_notification, montant, objet, max_date, file_date, json.dumps(json_data)))
                    marche_id = cursor.fetchone()[0]
            else:
                # Insérer le nouvel enregistrement
                cursor.execute("""
                    INSERT INTO decp.marche (marche_id, source_id, file_id, indx, id, acheteur, titulaires, date_notification, montant, objet, max_date, date_creation, data_in)
                    VALUES (nextval('decp.s_marche'), %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id, acheteur, titulaires, date_notification, montant) 
                    DO NOTHING
                    RETURNING marche_id;
                """, (source_id, file_id, index, id, acheteur, titulaires, date_notification, montant, objet, max_date, file_date, json.dumps(json_data)))
                marche_id = cursor.fetchone()[0]

            # Valider la transaction
            self.connection.commit()

        except Exception as e:
            logging.error(self.ERROR_MESSAGE_MARCHE + e)
            # Annuler la transaction en cas d'erreur
            self.connection.rollback()

        finally:
            # Fermeture systématique du curseur après utilisation
            cursor.close()

        return marche_id

    def update_marche(self, marche_id, json_data):
        try:
            cursor = self.connection.cursor()

            # Démarrer une transaction
            cursor.execute("BEGIN;")

           # Suppression du doublon
            cursor.execute("""
                UPDATE decp.marche,
                SET data_out = %s
                WHERE marche_id = %s
            """, (json.dumps(json_data),marche_id,))

            # Valider la transaction
            self.connection.commit()

        except Exception as e:
            logging.error(f"Erreur lors de l'ajout du marché en base: {e} ")
            # Annuler la transaction en cas d'erreur
            self.connection.rollback()

        finally:
            # Fermeture systématique du curseur après utilisation
            cursor.close()

    def bulk_update_marche(self, pairs, chunk_size=10000):
        """
        pairs: list of (marche_id (int), data_augmente (dict))
        chunk_size: number of rows to insert per execute_values call
        """
        try:
            with self.connection:
                with self.connection.cursor() as cur:
                    # create temp table that will be dropped at commit
                    cur.execute("""
                        CREATE TEMP TABLE tmp_updates(
                            marche_id bigint PRIMARY KEY,
                            data_out jsonb
                        ) ON COMMIT DROP;
                    """)

                    insert_sql = "INSERT INTO tmp_updates (marche_id, data_out) VALUES %s"
                    # insert in chunks
                    for i in range(0, len(pairs), chunk_size):
                        chunk = pairs[i:i + chunk_size]
                        values = [(mid, Json(j)) for mid, j in chunk]
                        execute_values(cur, insert_sql, values, page_size=1000)

                    # single UPDATE joining the temp table, only where not already retained
                    cur.execute("""
                        UPDATE decp.marche
                        SET data_out = t.data_out
                        FROM tmp_updates t
                        WHERE marche.marche_id = t.marche_id
                        RETURNING marche.marche_id;
                    """)
                    updated = [r[0] for r in cur.fetchall()]
                    return updated
        finally:
            cur.close()

    def bulk_update_marche_augmente(self, pairs, chunk_size=10000):
        """
        pairs: list of (marche_id (int), data_augmente (dict))
        chunk_size: number of rows to insert per execute_values call
        """
        try:
            with self.connection:
                with self.connection.cursor() as cur:
                    # create temp table that will be dropped at commit
                    cur.execute("""
                        CREATE TEMP TABLE tmp_updates(
                            marche_id bigint PRIMARY KEY,
                            data_augmente jsonb
                        ) ON COMMIT DROP;
                    """)

                    insert_sql = "INSERT INTO tmp_updates (marche_id, data_augmente) VALUES %s"
                    # insert in chunks
                    for i in range(0, len(pairs), chunk_size):
                        chunk = pairs[i:i + chunk_size]
                        values = [(mid, Json(j)) for mid, j in chunk]
                        execute_values(cur, insert_sql, values, page_size=1000)

                    # single UPDATE joining the temp table, only where not already retained
                    cur.execute("""
                        UPDATE decp.marche
                        SET data_augmente = t.data_augmente,
                            est_retenu = TRUE
                        FROM tmp_updates t
                        WHERE marche.marche_id = t.marche_id
                        AND marche.est_retenu IS NOT TRUE
                        RETURNING marche.marche_id;
                    """)
                    updated = [r[0] for r in cur.fetchall()]
                    return updated
        finally:
            cur.close()

    def update_marche_augmente(self, marche_id, json_data):
        try:
            cursor = self.connection.cursor()

            # Démarrer une transaction
            cursor.execute("BEGIN;")

           # Suppression du doublon
            cursor.execute("""
                UPDATE decp.marche 
                SET data_augmente = %s,
                    est_retenu = TRUE
                WHERE marche_id = %s
            """, (json.dumps(json_data),marche_id,))

            # Valider la transaction
            self.connection.commit()

        except Exception as e:
            print(f"Erreur lors de l'ajout du marché en base: {e} ")
            # Annuler la transaction en cas d'erreur
            self.connection.rollback()

        finally:
            # Fermeture systématique du curseur après utilisation
            cursor.close()

    # Gestion des concession

    def add_concession(self, source_id, file_id, file_date, index, id, autorite_concedante, concessionnaires, date_debut_execution, valeur_globale, objet, max_date, json_data):
        """
        Ajoute une concession si celui-ci n'existe pas déjà
        ou remplace une concession si celle-ci est retrouvée dans la table concession avec une date de 
        publication maximale (modifications) antérieure à celle de la concession en entrée
        :return: concession_id l'id de l'enregistrement ajouté
        """
        concession_id = None
        try:
            cursor = self.connection.cursor()

            # Démarrer une transaction
            cursor.execute("BEGIN;")

            # Retrouver un enregistrement potentiellement en doublon
            cursor.execute("""
                SELECT c.concession_id, c.max_date
                FROM decp.concession c
                WHERE (c.id = %s AND c.autorite_concedante = %s AND c.concessionnaires = %s AND c.date_debut_execution = %s AND c.valeur_globale = %s)
            """, (id, autorite_concedante, concessionnaires, date_debut_execution, valeur_globale,))
            result = cursor.fetchone()

            if result:
                found_concession_id = result[0]
                found_max_date = result[1]
                if found_max_date is not None and file_date<found_max_date:
                    # Insérer le nouvel enregistrement directement dans les doublons
                    cursor.execute("""
                        INSERT INTO decp.concession_doublon (concession_doublon_id, source_id, file_id, indx, id, autorite_concedante, concessionnaires, date_debut_execution, valeur_globale, objet, max_date, date_creation, data_in)
                        VALUES (nextval('decp.s_concession_doublon'), %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        RETURNING concession_id;
                    """, (source_id, file_id, index, id, autorite_concedante, concessionnaires, date_debut_execution, valeur_globale, objet, max_date, file_date, json.dumps(json_data)))
                    concession_id = 0

                else:
                    # Déplacer l'enregistrement en doublon existant
                    cursor.execute("""
                        INSERT INTO decp.concession_doublon (concession_doublon_id, concession_id, source_id, file_id, indx, id, autorite_concedante, concessionnaires, date_debut_execution, valeur_globale, objet, max_date, date_creation, data_in, data_out, est_retenu)
                        SELECT nextval('decp.s_concession_doublon'), c.concession_id, c.source_id, c.file_id, c.indx, c.id, c.autorite_concedante, c.concessionnaires, c.date_debut_execution, c.valeur_globale, c.objet, c.max_date, c.date_creation, c.data_in, c.data_out, c.est_retenu
                        FROM decp.concession c
                        WHERE (c.id = %s AND c.autorite_concedante = %s AND c.concessionnaires = %s AND c.date_debut_execution = %s AND c.valeur_globale = %s)
                    """, (id, autorite_concedante, concessionnaires, date_debut_execution, valeur_globale,))
            
                    # Suppression du doublon
                    cursor.execute("""
                        DELETE FROM decp.concession m
                        WHERE m.id = %s AND m.autorite_concedante = %s AND m.concessionnaires = %s AND m.date_debut_execution = %s AND m.valeur_globale = %s
                    """, (id, autorite_concedante, concessionnaires, date_debut_execution, valeur_globale,))
                    
                    # Insérer le nouvel enregistrement
                    cursor.execute("""
                        INSERT INTO decp.concession (concession_id, source_id, file_id, indx, id, autorite_concedante, concessionnaires, date_debut_execution, valeur_globale, objet, max_date, date_creation, data_in)
                        VALUES (nextval('decp.s_concession'), %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (id,  autorite_concedante, concessionnaires, date_debut_execution, valeur_globale) 
                        DO NOTHING
                        RETURNING concession_id;
                    """, (source_id, file_id, index, id, autorite_concedante, concessionnaires, date_debut_execution, valeur_globale, objet, max_date, file_date, json.dumps(json_data)))
                    concession_id = cursor.fetchone()[0]

            else:
                # Insérer le nouvel enregistrement
                cursor.execute("""
                    INSERT INTO decp.concession (concession_id, source_id, file_id, indx, id, autorite_concedante, concessionnaires, date_debut_execution, valeur_globale, objet, max_date, date_creation, data_in)
                    VALUES (nextval('decp.s_concession'), %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id,  autorite_concedante, concessionnaires, date_debut_execution, valeur_globale) 
                    DO NOTHING
                    RETURNING concession_id;
                """, (source_id, file_id, index, id, autorite_concedante, concessionnaires, date_debut_execution, valeur_globale, objet, max_date, file_date, json.dumps(json_data)))
                concession_id = cursor.fetchone()[0]

            # Valider la transaction
            self.connection.commit()

        except Exception as e:
            logging.error(self.ERROR_MESSAGE_CONCESSION + e)
            # Annuler la transaction en cas d'erreur
            self.connection.rollback()

        finally:
            # Fermeture systématique du curseur après utilisation
            cursor.close()

        return concession_id

    def update_concession(self, concession_id, json_data):
        try:
            cursor = self.connection.cursor()

            # Démarrer une transaction
            cursor.execute("BEGIN;")

           # Suppression du doublon
            cursor.execute("""
                UPDATE decp.concession
                SET data_out = %s
                WHERE concession_id = %s
            """, (json.dumps(json_data),concession_id,))

            # Valider la transaction
            self.connection.commit()

        except Exception as e:
            print(f"Erreur lors de l'ajout de la concession en base: {e} ")
            # Annuler la transaction en cas d'erreur
            self.connection.rollback()

        finally:
            # Fermeture systématique du curseur après utilisation
            cursor.close()

    def bulk_update_concession_augmente(self, pairs, chunk_size=10000):
        """
        pairs: list of (concessionid (int), data_augmente (dict))
        chunk_size: number of rows to insert per execute_values call
        """
        try:
            with self.connection:
                with self.connection.cursor() as cur:
                    # create temp table that will be dropped at commit
                    cur.execute("""
                        CREATE TEMP TABLE tmp_updates(
                            concession_id bigint PRIMARY KEY,
                            data_augmente jsonb
                        ) ON COMMIT DROP;
                    """)

                    insert_sql = "INSERT INTO tmp_updates (concession_id, data_augmente) VALUES %s"
                    # insert in chunks
                    for i in range(0, len(pairs), chunk_size):
                        chunk = pairs[i:i + chunk_size]
                        values = [(mid, Json(j)) for mid, j in chunk]
                        execute_values(cur, insert_sql, values, page_size=1000)

                    # single UPDATE joining the temp table, only where not already retained
                    cur.execute("""
                        UPDATE decp.concession
                        SET data_augmente = t.data_augmente,
                            est_retenu = TRUE
                        FROM tmp_updates t
                        WHERE concession.concession_id = t.concession_id
                        RETURNING concession.concession_id;
                    """)
                    updated = [r[0] for r in cur.fetchall()]
                    return updated
        finally:
            cur.close()

    def update_concession_augmente(self, concession_id, json_data):
        try:
            cursor = self.connection.cursor()

            # Démarrer une transaction
            cursor.execute("BEGIN;")

           # Suppression du doublon
            cursor.execute("""
                UPDATE decp.concession 
                SET data_augmente = %s,
                    est_retenu = TRUE
                WHERE concession_id = %s
                AND NOT est_retenu IS TRUE
            """, (json.dumps(json_data),concession_id,))

            # Valider la transaction
            self.connection.commit()

        except Exception as e:
            print(f"Erreur lors de l'ajout de la concession en base: {e} ")
            # Annuler la transaction en cas d'erreur
            self.connection.rollback()

        finally:
            # Fermeture systématique du curseur après utilisation
            cursor.close()
    
    # Methodes utiles

    def extract_json_to_file_for_month(self,file_path:str,ref_date: str):
        """
        Génère le fichier decp-global.json à partir des enregistrements 
        des tables marché et concession ayant un data_out non null (données valides et nettoyées dans decp-rama)
        """
        sub_query = ""
        if ref_date is not None:
            file_path = file_path.replace('.','-'+ref_date+'.')
            sub_query = f"AND substring(max_date,1,7)='{ref_date}'"
        keep_db_id = ref_date is not None
        logging.info (f"Launching generation for {file_path}")
        try:
            utilsJson = UtilsJson()

            # Connect to the PostgreSQL database
            cursor = self.connection.cursor()

            # Query to select the JSON data from the 'marche' table
            query = f"SELECT data_out FROM decp.marche WHERE data_out is not null {sub_query}" # AND est_retenu is TRUE"

            # Execute the query
            cursor.execute(query)

            # Fetch all results
            json_marche = cursor.fetchall()

            # Query to select the JSON data from the 'marche' table
            query = f"SELECT data_out FROM decp.concession WHERE data_out is not null {sub_query}" # and concession_id =0"

            # Execute the query
            cursor.execute(query)

            # Fetch all results
            json_concession = cursor.fetchall()

            # Write to file
            with open(file_path, 'w') as outfile:
                outfile.write('{\n  "marches": {\n    "marche": [')
                i = 0
                for row in json_marche:
                    outfile.write((',' if i > 0 else '') + '\n')
                    json.dump(utilsJson.format_json(row[0], keep_db_id), outfile)
                    i += 1

                if ref_date is None:
                    outfile.write('\n    ],\n "contrat-concession": [\n')
                    i=0
                    
                for row in json_concession:
                    outfile.write((',' if i > 0 else '') + '\n')
                    json.dump(utilsJson.format_json(row[0], keep_db_id), outfile)
                    i += 1
                outfile.write('\n    ]\n  }\n}')
                
        except Exception as e:
            print(f"Error: {e}")
        finally:
            # Close the database connection
            cursor.close()
        logging.info (f"{file_path} created")
        
    def extract_json_to_file(self,file_path:str,generate_month=True):
        if generate_month:
            start_year, start_month = 2024, 1
            today = date.today()  
            end_year, end_month = today.year, today.month

            # Sauvegarde des marchés et concessions uniques regroupées par année et mois de date de 
            year, month = start_year, start_month
            while (year, month) <= (end_year, end_month):
                ref_date = f"{year}-{month:02d}"
                self.extract_json_to_file_for_month(file_path,ref_date)
                if month == 12:
                    year += 1
                    month = 1
                else:
                    month += 1

        self.extract_json_to_file_for_month(file_path,None)

    def close(self):
        self.connection.close()
