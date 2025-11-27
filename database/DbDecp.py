import json
import locale
import logging
import os
import psycopg2
import pandas as pd
from dotenv import load_dotenv
from psycopg2 import sql
from os import environ as env

logging.getLogger('db').propagate = False
logger = logging.getLogger(__name__)
locale.setlocale(locale.LC_ALL, 'fr_FR.UTF-8')

# Classe d'accès à la base de données
# Défini la logique de dédoublonnage des données et l' ajout des enregistrements de marché et de concession 
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


    def find_or_add_source(self, source_name:str, dataset_id:str):
        """
        Recherche une source par son nom et l'ajoute si elle n'existe pas.
        :param source_id: INT8, identifiant de la source
        :param nb: INT8, Nombre d'enregistrement dans la source
        """
        source_id = None
        try:
            cursor = self.connection.cursor()
            
            cursor.execute("SELECT source_id FROM public.source WHERE nom = %s", (source_name,))
            result = cursor.fetchone()

            if result:
                source_id = result[0]
            else:
                cursor.execute("INSERT INTO public.source (source_id, nom, dataset_id, date_creation) VALUES (nextval('public.s_source'), %s, %s, NOW()) RETURNING source_id", (source_name,dataset_id))
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
        Recherche un fichier par son nom et l'ajoute s'il n'existe pas.
        :param source_id: INT8, identifiant de la source
        :param nb: INT8, Nombre d'enregistrement dans la source
        """
        file_id = None
        try:
            cursor = self.connection.cursor()
            
            cursor.execute("SELECT file_id FROM public.file WHERE nom = %s and source_id = %s", (file_name,source_id,))
            result = cursor.fetchone()

            if result:
                file_id = result[0]
            else:
                cursor.execute("INSERT INTO public.file (file_id, nom, source_id, nb_marches, nb_concessions, date_creation) VALUES (nextval('public.s_file'), %s, %s, %s, %s, NOW()) RETURNING file_id", (file_name, source_id, nb_marches, nb_concessions))
                file_id = cursor.fetchone()[0]

            self.connection.commit()

        except Exception as e:
            logging.error(self.ERROR_MESSAGE_FILE, e)
        finally:
            # Fermeture systématique du curseur après utilisation
            cursor.close()

        return file_id

    # Ajoute un marché si celui-ci n'existe pas déjà
    # ou remplace un marché si celui-ci est retrouvé dans la table marché avec une date de 
    # publication maximale (modifications,acteSousTraitqnceModification) antérieure à celle du marché en entrée
    def add_marche(self, source_id, file_id, index, id, acheteur, titulaires, date_notification, montant, objet, max_date, json_data):
        marche_id = None
        try:
            cursor = self.connection.cursor()

            # Démarrer une transaction
            cursor.execute("BEGIN;")

            cursor.execute("""
                SELECT m.marche_id, m.source_id, m.file_id, m.indx, m.id, m.acheteur, m.titulaires, m.date_notification, m.montant, m.objet, m.max_date
                FROM public.marche m
                WHERE (m.id = %s AND m.acheteur = %s AND m.titulaires = %s AND m.date_notification = %s AND m.montant = %s)
            """, (id, acheteur, titulaires, date_notification, montant,))
            result = cursor.fetchone()

            if result:
                found_marche_id = result[0]
                found_max_date = result[10]
                # reprise globale >= si la date es la même on considère que le premier ibséré (cad le dernier en date de fichier) edt le bln, le reste est en doublon
                # au jour le jour >
                if found_max_date >= max_date:
                    # Insérer le nouvel enregistrement
                    cursor.execute("""
                        INSERT INTO marche_doublon (marche_doublon_id, source_id, file_id, indx, id, acheteur, titulaires, date_notification, montant, objet, max_date, data_in)
                        VALUES (nextval('public.s_marche_doublon'), %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        RETURNING marche_id;
                    """, (source_id, file_id, index, id, acheteur, titulaires, date_notification, montant, objet, max_date, json.dumps(json_data)))
                    marche_id = 0

                else:
                    # Déplacer l'enregistrement en doublon si existant
                    cursor.execute("""
                        INSERT INTO public.marche_doublon (marche_doublon_id, marche_id, source_id, file_id, indx, id, acheteur, titulaires, date_notification, montant, objet, max_date, data_in, data_out, est_retenu)
                        SELECT nextval('public.s_marche_doublon'), m.marche_id, m.source_id, m.file_id, m.indx, m.id, m.acheteur, m.titulaires, m.date_notification, m.montant, m.objet, m.max_date, m.data_in, m.data_out, m.est_retenu
                        FROM public.marche m
                        WHERE (m.id = %s AND m.acheteur = %s AND m.titulaires = %s AND m.date_notification = %s AND m.montant = %s)
                    """, (id, acheteur, titulaires, date_notification, montant,))

                    # Suppression du doublon
                    cursor.execute("""
                        DELETE FROM public.marche m
                        WHERE m.id = %s AND m.acheteur = %s AND m.titulaires = %s AND m.date_notification = %s AND m.montant = %s
                    """, (id, acheteur, titulaires, date_notification, montant,))

                    # Insérer le nouvel enregistrement
                    cursor.execute("""
                        INSERT INTO marche (marche_id, source_id, file_id, indx, id, acheteur, titulaires, date_notification, montant, objet, max_date, data_in)
                        VALUES (nextval('public.s_marche'), %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (id, acheteur, titulaires, date_notification, montant) 
                        DO NOTHING
                        RETURNING marche_id;
                    """, (source_id, file_id, index, id, acheteur, titulaires, date_notification, montant, objet, max_date, json.dumps(json_data)))
                    marche_id = cursor.fetchone()[0]
            else:
                # Insérer le nouvel enregistrement
                cursor.execute("""
                    INSERT INTO marche (marche_id, source_id, file_id, indx, id, acheteur, titulaires, date_notification, montant, objet, max_date, data_in)
                    VALUES (nextval('public.s_marche'), %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id, acheteur, titulaires, date_notification, montant) 
                    DO NOTHING
                    RETURNING marche_id;
                """, (source_id, file_id, index, id, acheteur, titulaires, date_notification, montant, objet, max_date, json.dumps(json_data)))
                marche_id = cursor.fetchone()[0]

            # Valider la transaction
            self.connection.commit()

        except Exception as e:
            print(f"Erreur lors de l'ajout du marché en base: {e} ")
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
                UPDATE public.marche 
                SET data_out = %s
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

    # Ajoute une concession si celui-ci n'existe pas déjà
    # ou remplace une concession si celle-ci est retrouvée dans la table concession avec une date de 
    # publication maximale (modifications) antérieure à celle de la concession en entrée
    def add_concession(self, source_id, file_id, index, id, autorite_concedante, concessionnaires, date_debut_execution, valeur_globale, objet, max_date, json_data):
        concession_id = None
        try:
            cursor = self.connection.cursor()

            # Démarrer une transaction
            cursor.execute("BEGIN;")

            # Déplacer l'enregistrement en doublon si existant
            cursor.execute("""
                SELECT c.concession_id, c.source_id, c.file_id, c.indx, c.id, c.autorite_concedante, c.concessionnaires, c.date_debut_execution, c.valeur_globale, c.objet, c.max_date
                FROM public.concession c
                WHERE (c.id = %s AND c.autorite_concedante = %s AND c.concessionnaires = %s AND c.date_debut_execution = %s AND c.valeur_globale = %s)
            """, (id, autorite_concedante, concessionnaires, date_debut_execution, valeur_globale,))
            result = cursor.fetchone()

            if result:
                found_concession_id = result[0]
                found_max_date = result[10]
                if found_max_date >= max_date:
                    # Insérer le nouvel enregistrement
                    cursor.execute("""
                        INSERT INTO concession_doublon (concession_doublon_id, source_id, file_id, indx, id, autorite_concedante, concessionnaires, date_debut_execution, valeur_globale, objet, max_date, data_in)
                        VALUES (nextval('public.s_concession_doublon'), %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        RETURNING concession_id;
                    """, (source_id, file_id, index, id, autorite_concedante, concessionnaires, date_debut_execution, valeur_globale, objet, max_date, json.dumps(json_data)))
                    concession_id = 0

                else:
                    # Déplacer l'enregistrement en doublon existant
                    cursor.execute("""
                        INSERT INTO public.concession_doublon (concession_doublon_id, concession_id, source_id, file_id, indx, id, autorite_concedante, concessionnaires, date_debut_execution, valeur_globale, objet, max_date, data_in, data_out, est_retenu)
                        SELECT nextval('public.s_concession_doublon'), c.concession_id, c.source_id, c.file_id, c.indx, c.id, c.autorite_concedante, c.concessionnaires, c.date_debut_execution, c.valeur_globale, c.objet, c.max_date, c.data_in, c.data_out, c.est_retenu
                        FROM public.concession c
                        WHERE (c.id = %s AND c.autorite_concedante = %s AND c.concessionnaires = %s AND c.date_debut_execution = %s AND c.valeur_globale = %s)
                    """, (id, autorite_concedante, concessionnaires, date_debut_execution, valeur_globale,))
            
                    # Suppression du doublon
                    cursor.execute("""
                        DELETE FROM public.concession m
                        WHERE m.id = %s AND m.autorite_concedante = %s AND m.concessionnaires = %s AND m.date_debut_execution = %s AND m.valeur_globale = %s
                    """, (id, autorite_concedante, concessionnaires, date_debut_execution, valeur_globale,))
                    
                    # Insérer le nouvel enregistrement
                    cursor.execute("""
                        INSERT INTO concession (concession_id, source_id, file_id, indx, id, autorite_concedante, concessionnaires, date_debut_execution, valeur_globale, objet, max_date, data_in)
                        VALUES (nextval('public.s_concession'), %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (id,  autorite_concedante, concessionnaires, date_debut_execution, valeur_globale) 
                        DO NOTHING
                        RETURNING concession_id;
                    """, (source_id, file_id, index, id, autorite_concedante, concessionnaires, date_debut_execution, valeur_globale, objet, max_date,json.dumps(json_data)))
                    concession_id = cursor.fetchone()[0]

            else:
                # Insérer le nouvel enregistrement
                cursor.execute("""
                    INSERT INTO concession (concession_id, source_id, file_id, indx, id, autorite_concedante, concessionnaires, date_debut_execution, valeur_globale, objet, max_date, data_in)
                    VALUES (nextval('public.s_concession'), %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id,  autorite_concedante, concessionnaires, date_debut_execution, valeur_globale) 
                    DO NOTHING
                    RETURNING concession_id;
                """, (source_id, file_id, index, id, autorite_concedante, concessionnaires, date_debut_execution, valeur_globale, objet, max_date,json.dumps(json_data)))
                concession_id = cursor.fetchone()[0]

            # Valider la transaction
            self.connection.commit()

        except Exception as e:
            print(f"Erreur lors de l'ajout de la concession en base: {e} ")
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
                UPDATE public.concession 
                SET data_out = %s
                WHERE marche_id = %s
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

    def _clean_json(self,marche):
        def _restore_attributes_by_prefix(self,marche,prefix):
            keys_to_delete = [clé for clé in marche.keys() if clé.startswith(prefix)]
            for key in keys_to_delete:
                if marche[key] == 'NC':
                    marche[key[len(prefix):]] = marche[key]
                if not pd.isna(marche[key]):
                    marche[key[len(prefix):]] = marche[key]
                del marche[key]

        def _restore_attributes_by_prefix_in_node(self,marche,node_parent:str,node_child:str,prefix:str):
            if node_parent in marche and isinstance(marche[node_parent],list):
                for element in marche[node_parent]:
                    if node_child in element and isinstance(element[node_child],dict):
                        self._restore_attributes_by_prefix(element[node_child],prefix)

        def force_int_or_nc(self,cle:str,marche:dict):
            if cle in marche.keys() and marche[cle] != 'NC':
                try:
                    # Convertir la valeur en entier
                    marche[cle] = int(marche[cle])
                except ValueError:
                    None
                    #logging.warning(f"Erreur : la valeur de la clé '{cle}' ne peut pas être convertie en entier.")
                except TypeError:
                    logging.warning(f"Erreur : la valeur de la clé '{cle}' est de type incompatible pour la conversion.")

        def force_bool_or_nc(self,cle:str,marche:dict):
            if cle in marche.keys() and marche[cle] != 'NC':
                if ("true"==marche[cle]) or ("oui"==marche[cle]) or ("1"==marche[cle]):
                    marche[cle] = True
                elif ("false"==marche[cle]) or ("non"==marche[cle]) or ("0"==marche[cle]):
                    marche[cle] = False

        def delete_attributes_by_prefix(marche,prefix):
            keys_to_delete = [clé for clé in marche.keys() if clé.startswith(prefix)]
            for key in keys_to_delete:
                del marche[key]
            delete_attributes_by_prefix(marche,'report__')
            delete_attributes_by_prefix(marche,'tmp__')

            if 'idAccordCadre' in marche and (marche['idAccordCadre'] == '' or pd.isna(marche['idAccordCadre'])):
                del marche["idAccordCadre"]
            if 'origineUE' in marche and (marche['origineUE'] == '' or pd.isna(marche['origineUE'])):
                del marche["origineUE"]
            if 'origineFrance' in marche and (marche['origineFrance'] == '' or pd.isna(marche['origineFrance'])):
                del marche["origineFrance"]
            if 'tauxAvance' in marche and (marche['tauxAvance'] == '' or pd.isna(marche['tauxAvance'])):
                del marche["tauxAvance"]

            if 'modifications' in marche and isinstance(marche['modifications'],list) and len(marche['modifications'])==0:
                del marche['modifications']                
            if 'actesSousTraitance' in marche \
                and ((isinstance(marche['actesSousTraitance'],list) and len(marche['actesSousTraitance'])==0) \
                    or (isinstance(marche['actesSousTraitance'],str) and marche['actesSousTraitance']=='') or \
                    (not isinstance(marche['actesSousTraitance'],list) and pd.isna(marche['actesSousTraitance']))):
                del marche['actesSousTraitance']  
            if 'modificationsActesSousTraitance' in marche \
                and ((isinstance(marche['modificationsActesSousTraitance'],list) and len(marche['modificationsActesSousTraitance'])==0) \
                    or (isinstance(marche['modificationsActesSousTraitance'],str) and marche['modificationsActesSousTraitance']=='') or \
                    (not isinstance(marche['modificationsActesSousTraitance'],list) and pd.isna(marche['modificationsActesSousTraitance']))):
                del marche['modificationsActesSousTraitance']  

            if 'backup__montant' in marche:
                marche['montant'] = marche['backup__montant']
                del marche['backup__montant']
            if 'backup__datePublicationDonnees' in marche:
                if not pd.isnull(marche['backup__datePublicationDonnees']):
                    marche['datePublicationDonnees'] = marche['backup__datePublicationDonnees']
                del marche['backup__datePublicationDonnees']
            
            self._restore_attributes_by_prefix(marche,'backup__')
            self._restore_attributes_by_prefix_in_node(marche,'actesSousTraitance','acteSousTraitance','backup__')

            self.force_int_or_nc('dureeMois',marche)
            self.force_int_or_nc('offresRecues',marche)
            self.force_bool_or_nc('marcheInnovant',marche)
            self.force_bool_or_nc('attributionAvance',marche)
            self.force_bool_or_nc('sousTraitanceDeclaree',marche)

            if '_type' in marche and marche['_type'] != 'Marché':
                if 'montant' in marche:
                    del marche["montant"]
                if 'offresRecues' in marche:
                    del marche["offresRecues"]
                if '_type' in marche:
                    del marche["_type"]
            else:
                if 'valeurGlobale' in marche:
                    del marche["valeurGlobale"]
                if 'dateSignature' in marche:
                    del marche["dateSignature"]
                if 'donneesExecution' in marche:
                    del marche["donneesExecution"]
                if 'concessionnaires' in marche:
                    del marche["concessionnaires"]
                if 'autoriteConcedante' in marche:
                    del marche["autoriteConcedante"]
                if 'dateDebutExecution' in marche:
                    del marche["dateDebutExecution"]
                if 'montantSubventionPublique' in marche:
                    del marche["montantSubventionPublique"]
                if '_type' in marche:
                    del marche["_type"]

        return marche
    
    def extract_json_to_file(self,file_path:str):

        try:

            # Connect to the PostgreSQL database
            cursor = self.connection.cursor()

            # Query to select the JSON data from the 'marche' table
            query = "SELECT data_out FROM marche WHERE data_out is not null"

            # Execute the query
            cursor.execute(query)

            # Fetch all results
            json_marche = cursor.fetchall()

            # Query to select the JSON data from the 'marche' table
            query = "SELECT data_out FROM concession WHERE data_out is not null"

            # Execute the query
            cursor.execute(query)

            # Fetch all results
            json_concession = cursor.fetchall()

            # Write to file
            with open(file_path, 'w') as outfile:
                outfile.write('{\n  "marches": {\n    "marche": [')
                i = 0
                for row in json_marche:
                    if i>0:
                        outfile.write(',\n')
                    else:
                        outfile.write('\n')
                    json.dump(self._clean_json(row[0]), outfile)
                    i += 1
                outfile.write('\n    ]\n  },\n  {"concession": [\n')
                i = 0
                for row in json_concession:
                    if i>0:
                        outfile.write(',\n')
                    else:
                        outfile.write('\n')
                    json.dump(self._clean_json(row[0]), outfile)
                    i += 1
                outfile.write('\n    ]\n  }\n}')
                
        except Exception as e:
            print(f"Error: {e}")
        finally:
            # Close the database connection
            cursor.close()

    def close(self):
        self.connection.close()

    def add_marche_simple(self, source_id, file_id, index, id, acheteur, titulaires, date_notification, montant, objet, max_date, json_data):
        marche_id = None
        try:
            cursor = self.connection.cursor()

            # Démarrer une transaction
            cursor.execute("BEGIN;")

            # Déplacer l'enregistrement en doublon si existant
            cursor.execute("""
                INSERT INTO public.marche_doublon (marche_doublon_id, marche_id, source_id, file_id, indx, id, acheteur, titulaires, date_notification, montant, objet, data_in, data_out)
                SELECT nextval('public.s_marche_doublon'), m.marche_id, m.source_id, m.file_id, m.indx, m.id, m.acheteur, m.titulaires, m.date_notification, m.montant, m.objet, m.data_in, m.data_out
                FROM public.marche m
                WHERE (m.id = %s AND m.acheteur = %s AND m.titulaires = %s AND m.date_notification = %s AND m.montant = %s and m.max_date < %s)
            """, (id, acheteur, titulaires, date_notification, montant,max_date,))

            # Suppression du doublon
            cursor.execute("""
                DELETE FROM public.marche m
                WHERE m.id = %s AND m.acheteur = %s AND m.titulaires = %s AND m.date_notification = %s AND m.montant = %s AND m.max_date < %s
            """, (id, acheteur, titulaires, date_notification, montant,max_date,))

            # Insérer le nouvel enregistrement
            cursor.execute("""
                INSERT INTO marche (marche_id, source_id, file_id, indx, id, acheteur, titulaires, date_notification, montant, objet, data_in)
                VALUES (nextval('public.s_marche'), %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id, acheteur, titulaires, date_notification, montant,max_date) 
                DO NOTHING
                RETURNING marche_id;
            """, (source_id, file_id, index, id, acheteur, titulaires, date_notification, montant, objet, json.dumps(json_data)))
            marche_id = cursor.fetchone()[0]

            # Valider la transaction
            self.connection.commit()

        except Exception as e:
            print(f"Erreur lors de l'ajout du marché en base: {e} ")
            # Annuler la transaction en cas d'erreur
            self.connection.rollback()

        finally:
            # Fermeture systématique du curseur après utilisation
            cursor.close()

        return marche_id

    def add_concession_simple(self, source_id, file_id, index, id, autorite_concedante, concessionnaires, date_debut_execution, valeur_globale, objet, json_data):
        concession_id = None
        try:
            cursor = self.connection.cursor()

            # Démarrer une transaction
            cursor.execute("BEGIN;")

            # Déplacer l'enregistrement en doublon si existant
            cursor.execute("""
                INSERT INTO public.concession_doublon (concession_doublon_id, concession_id, source_id, file_id, indx, id, autorite_concedante, concessionnaires, date_debut_execution, valeur_globale, objet, data_in, data_out)
                SELECT nextval('public.s_concession_doublon'), c.concession_id, c.source_id, c.file_id, c.indx, c.id, c.autorite_concedante, c.concessionnaires, c.date_debut_execution, c.valeur_globale, c.objet, c.data_in, c.data_out
                FROM public.concession c
                WHERE (c.id = %s AND c.autorite_concedante = %s AND c.concessionnaires = %s AND c.date_debut_execution = %s AND c.valeur_globale = %s)
            """, (id, autorite_concedante, concessionnaires, date_debut_execution, valeur_globale,))

            # Suppression du doublon
            cursor.execute("""
                DELETE FROM public.concession m
                WHERE m.id = %s AND m.autorite_concedante = %s AND m.concessionnaires = %s AND m.date_debut_execution = %s AND m.valeur_globale = %s
            """, (id, autorite_concedante, concessionnaires, date_debut_execution, valeur_globale,))

            # Insérer le nouvel enregistrement
            cursor.execute("""
                INSERT INTO concession (concession_id, source_id, file_id, indx, id, autorite_concedante, concessionnaires, date_debut_execution, valeur_globale, objet, data_in)
                VALUES (nextval('public.s_concession'), %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id,  autorite_concedante, concessionnaires, date_debut_execution, valeur_globale) 
                DO NOTHING
                RETURNING concession_id;
            """, (source_id, file_id, index, id, autorite_concedante, concessionnaires, date_debut_execution, valeur_globale, objet, json.dumps(json_data)))
            concession_id = cursor.fetchone()[0]

            # Valider la transaction
            self.connection.commit()

        except Exception as e:
            print(f"Erreur lors de l'ajout de la concession en base: {e} ")
            # Annuler la transaction en cas d'erreur
            self.connection.rollback()

        finally:
            # Fermeture systématique du curseur après utilisation
            cursor.close()

        return concession_id
