import logging
import pandas as pd

class UtilsJson:

    def format_json(self,marche,keep_db_id:bool):
        """
        Return json with initia values NC and delete extra columns
        :return: marche un arché ou une concession au format json
        """
        def restore_attributes_by_prefix(marche,prefix):
            keys_to_delete = [clé for clé in marche.keys() if clé.startswith(prefix)]
            for key in keys_to_delete:
                if marche[key] == 'NC':
                    marche[key[len(prefix):]] = marche[key]
                if not pd.isna(marche[key]):
                    marche[key[len(prefix):]] = marche[key]
                del marche[key]

        def restore_attributes_by_prefix_in_node(marche,node_parent:str,node_child:str,prefix:str):
            if node_parent in marche and isinstance(marche[node_parent],list):
                for element in marche[node_parent]:
                    if node_child in element and isinstance(element[node_child],dict):
                        restore_attributes_by_prefix(element[node_child],prefix)

        def force_int_or_nc(cle:str,marche:dict):
            if cle in marche.keys() and marche[cle] != 'NC':
                try:
                    # Convertir la valeur en entier
                    marche[cle] = int(float(marche[cle]))
                except ValueError:
                    None
                    #logging.warning(f"Erreur : la valeur de la clé '{cle}' ne peut pas être convertie en entier.")
                except TypeError:
                    logging.warning(f"Erreur : la valeur de la clé '{cle}' est de type incompatible pour la conversion.")

        def force_bool_or_nc(cle:str,marche:dict):
            if cle in marche.keys() and marche[cle] != 'NC':
                if ("True"==marche[cle]) or ("true"==marche[cle]) or ("oui"==marche[cle]) or ("1"==marche[cle]):
                    marche[cle] = True
                elif ("False"==marche[cle]) or ("false"==marche[cle]) or ("non"==marche[cle]) or ("0"==marche[cle]):
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
        
        restore_attributes_by_prefix(marche,'backup__')
        restore_attributes_by_prefix_in_node(marche,'actesSousTraitance','acteSousTraitance','backup__')

        force_int_or_nc('dureeMois',marche)
        force_int_or_nc('offresRecues',marche)
        force_int_or_nc('db_id',marche)
        force_bool_or_nc('marcheInnovant',marche)
        force_bool_or_nc('attributionAvance',marche)
        force_bool_or_nc('sousTraitanceDeclaree',marche)

        if '_type' in marche and marche['_type'] != 'Marché':
            if 'montant' in marche:
                del marche["montant"]
            if 'offresRecues' in marche:
                del marche["offresRecues"]
            #if '_type' in marche:
            #    del marche["_type"]
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
            #if '_type' in marche:
            #    del marche["_type"]
        
        if not keep_db_id:
            del marche["db_id"]

        return marche
