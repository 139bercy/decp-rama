import logging

class NodeFormat:
    def is_normalized_list_node(dico, parent_node, child_node) -> bool:
        if parent_node in dico:
            parent_dico = dico[parent_node]
            if parent_dico is not None and isinstance(parent_dico, list) and len(parent_dico) > 0:
                for element in parent_dico:
                    # Vérifie si l'élément est un dictionnaire et si le noeud child_node y existe
                    if element is not None and child_node in element and isinstance(element, dict) and isinstance(element[child_node],dict): 
                        return True
        return False

    def normalize_list_node(marche, parent_node, child_node):
        # If array is into the child element move array to replace parent_node list
        if parent_node in marche.keys() and marche[parent_node] is not None \
            and len(marche[parent_node]) > 0 and isinstance( marche[parent_node],list) \
            and marche[parent_node][0] is not None \
            and child_node in marche[parent_node][0].keys() and isinstance(marche[parent_node][0][child_node],list):
            if 'modificationActesSousTraitance' == child_node:
                child_node_forced = 'modificationActeSousTraitance'
            else:
                child_node_forced = child_node
            nc = []
            for element in marche[parent_node][0][child_node]:
                if 'modifications' == parent_node and 'titulaires' in element.keys() \
                    and not NodeFormat.is_normalized_list_node(element,'titulaires', 'titulaire'):
                    NodeFormat.normalize_list_node(element,'titulaires', 'titulaire')
                nc.append({child_node_forced: element})
            marche[parent_node] = nc
        if parent_node in marche.keys() and marche[parent_node] is not None \
            and len(marche[parent_node]) > 0 and isinstance( marche[parent_node],list) \
            and marche[parent_node][0] is not None \
            and child_node in marche[parent_node][0].keys() and isinstance(marche[parent_node][0][child_node],dict) \
            and 'modificationActesSousTraitance' == child_node:
            marche[parent_node][0]={'modificationActeSousTraitance':marche[parent_node][0][child_node]}
        if 'modificationActesSousTraitance' != child_node:
            if parent_node in marche.keys() and marche[parent_node] is not None and len(
                marche[parent_node]) > 0 and isinstance( marche[parent_node],list):
                for i in range(len((marche[parent_node]))):
                    if isinstance( marche[parent_node][i],dict) and child_node not in marche[parent_node][i].keys():
                        marche[parent_node][i] = { child_node: marche[parent_node][i] }


    def normalize_list_node_inside(marche, parent_node_inside, child_node_inside, parent_node, child_node):
        if parent_node in marche:
            for i in range(len((marche[parent_node]))):
                if child_node in marche[parent_node][i] \
                    and parent_node_inside in marche[parent_node][i][child_node] \
                    and isinstance(marche[parent_node][i][child_node][parent_node_inside],list) \
                    and child_node_inside in marche[parent_node][i][child_node][parent_node_inside][0]:
                        marche[parent_node][i][child_node][parent_node_inside] = \
                            [{child_node_inside: element} for element in marche[parent_node][i][child_node][parent_node_inside][0][child_node_inside]]


    def is_normalized_list_value(dico, parent_node, child_node) -> bool:
        if parent_node in dico:
            parent_dico = dico[parent_node]
            if isinstance(parent_dico, list) and len(parent_dico)==1 and isinstance(parent_dico[0], dict) and len(parent_dico[0])==1:
                for element in parent_dico[0]:
                    # Vérifie si l'élément est un dictionnaire et si le noeud child_node y existe
                    if child_node in element and isinstance(element, str):
                        return True
        return False


    def normalize_list_value(marche, parent_node, child_node):
        """
        Corrige les noeuds de type liste qui sont au "mauvais" format>
        Format attendu:
        {
            "elements": 
                {
                    "element": [...<value>...] 
                }
            
        }
        
        """ 
        # Le noeuds enfant n'est pas une liste (Ex.: {"techniques": {"technique": "Sans objet"}} va devenir {"techniques": [ {"technique": "Sans objet"} ] } )
        if parent_node in marche.keys() and isinstance( marche[parent_node],dict) and \
            child_node in marche[parent_node].keys():
            if not isinstance(marche[parent_node][child_node],list):
                marche[parent_node][child_node] = [marche[parent_node][child_node]]
        if parent_node in marche.keys() and marche[parent_node] is not None and len(
            marche[parent_node]) > 0 and isinstance( marche[parent_node],list):
            for i in range(len((marche[parent_node]))):
                if isinstance( marche[parent_node][i],dict) and child_node not in marche[parent_node][i].keys():
                    marche[parent_node][i] = { child_node: marche[parent_node][i] }
        #elif parent_node in marche.keys() and isinstance( marche[parent_node],dict):
        #    if child_nodcec89a41-234c-4583-8900-acee2221675fe in marche[parent_node]:
        #        marche[parent_node][child_node] = [marche[parent_node][child_node]]

    def convert_ints(marche, parent_node, child_node):
        if parent_node in marche.keys() and marche[parent_node] is not None and len(
            marche[parent_node]) > 0 and isinstance( marche[parent_node],list):
            for i in range(len((marche[parent_node]))):
                if isinstance( marche[parent_node][i],dict) and child_node in marche[parent_node][i].keys():
                    NodeFormat.force_ints(['id','dureeMois'],marche[parent_node][i][child_node])
                    NodeFormat.force_floats(['montant'],marche[parent_node][i][child_node])


    def force_bools_nc(keys:list,marche:dict):
        for key in keys:
            if key in marche and marche[key] is not None and  marche[key] !='NC':
                if marche[key] == '0':
                    marche[key] = False
                elif marche[key] == '1':
                    marche[key] = True


    def force_bools(keys:list,marche:dict):
        for key in keys:
            if key in marche and marche[key] is not None:
                if marche[key] == '0' or marche[key] == 'non' or marche[key] == 'false' :
                    marche[key] = False
                elif marche[key] == '1' or marche[key] == 'oui' or marche[key] == 'true' :
                    marche[key] = True


    def force_floats_nc(keys:list,marche:dict):
        for key in keys:
            if key in marche and marche[key] is not None and  marche[key] !='NC':
                try:
                    # Convertir la valeur en float
                    marche[key] = float(marche[key])
                except ValueError:
                    logging.warning(f"Erreur : la valeur de la clé '{key}' {marche[key]} ne peut pas être convertie en entier.")
                except TypeError:
                    logging.warning(f"Erreur : la valeur de la clé '{key}' {marche[key]} est de type incompatible pour la conversion.")
            elif key in marche and marche[key] !='NC':
                marche[key] = 0

    def force_floats(keys:list,marche:dict):
        for key in keys:
            if key in marche and marche[key] is not None and  marche[key] !='NC':
                try:
                    # Convertir la valeur en float
                    marche[key] = float(marche[key])
                except ValueError:
                    logging.warning(f"Erreur : la valeur de la clé '{key}' ne peut pas être convertie en entier.")
                except TypeError:
                    logging.warning(f"Erreur : la valeur de la clé '{key}' est de type incompatible pour la conversion.")

    def force_ints_nc(keys:list,marche:dict):
        for key in keys:
            if key in marche and marche[key] is not None and  marche[key] !='NC':
                try:
                    # Convertir la valeur en int
                    marche[key] = int(marche[key])
                except ValueError:
                    logging.warning(f"Erreur : la valeur de la clé '{key}' ne peut pas être convertie en entier.")
                except TypeError:
                    logging.warning(f"Erreur : la valeur de la clé '{key}' est de type incompatible pour la conversion.")
            elif key in marche and marche[key] !='NC':
                marche[key] = 0

    def force_ints(keys:list,marche:dict):
        for key in keys:
            if key in marche and marche[key] is not None and  marche[key] !='NC':
                try:
                    # Convertir la valeur en int
                    marche[key] = int(marche[key])
                except ValueError:
                    logging.warning(f"Erreur : la valeur de la clé '{key}' ne peut pas être convertie en entier.")
                except TypeError:
                    logging.warning(f"Erreur : la valeur de la clé '{key}' est de type incompatible pour la conversion.")
