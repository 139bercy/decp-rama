
class NodeFormat:
    def is_normalized_list_node( dico, parent_node, child_node):
        if parent_node in dico:
            parent_dico = dico[parent_node]
            if isinstance(parent_dico, list) and len(parent_dico)==1:
                if isinstance(parent_dico[0], dict) and len(parent_dico[0])==1:
                    for element in parent_dico[0]:
                        # Vérifie si l'élément est un dictionnaire et si le noeud child_node y existe
                        if child_node in element and isinstance(element, dict): 
                            return True
        return False

    def normalize_list_node( marche, parent_node, child_node):
        # If array is into the child element move array to replace parent_node list
        if parent_node in marche.keys() and marche[parent_node] is not None \
            and len(marche[parent_node]) > 0 and isinstance( marche[parent_node],list) \
            and child_node in marche[parent_node][0].keys() and isinstance(marche[parent_node][0][child_node],list):
            if 'modificationActesSousTraitance' == child_node:
                child_node_forced = 'modificationActeSousTraitance'
            else:
                child_node_forced = child_node
            nc = []
            for element in marche[parent_node][0][child_node]:
                nc.append({child_node_forced: element})
            marche[parent_node] = nc
        if parent_node in marche.keys() and marche[parent_node] is not None \
            and len(marche[parent_node]) > 0 and isinstance( marche[parent_node],list) \
            and child_node in marche[parent_node][0].keys() and isinstance(marche[parent_node][0][child_node],dict) \
            and 'modificationActesSousTraitance' == child_node:
            marche[parent_node][0]={'modificationActeSousTraitance':marche[parent_node][0][child_node]}
        if not 'modificationActesSousTraitance' == child_node:
            if parent_node in marche.keys() and marche[parent_node] is not None and len(
                marche[parent_node]) > 0 and isinstance( marche[parent_node],list):
                for i in range(len((marche[parent_node]))):
                    if isinstance( marche[parent_node][i],dict) and child_node not in marche[parent_node][i].keys():
                        marche[parent_node][i] = { child_node: marche[parent_node][i] }

    def is_normalized_list_value(dico, parent_node, child_node):
        if parent_node in dico:
            parent_dico = dico[parent_node]
            if isinstance(parent_dico, list) and len(parent_dico)==1:
                if isinstance(parent_dico[0], dict) and len(parent_dico[0])==1:
                    for element in parent_dico[0]:
                        # Vérifie si l'élément est un dictionnaire et si le noeud child_node y existe
                        if child_node in element and isinstance(element, str):
                            return True
        return False


    def normalize_list_value( marche, parent_node, child_node):
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

    def convert_ints( marche, parent_node, child_node):
        if parent_node in marche.keys() and marche[parent_node] is not None and len(
            marche[parent_node]) > 0 and isinstance( marche[parent_node],list):
            for i in range(len((marche[parent_node]))):
                if isinstance( marche[parent_node][i],dict) and child_node in marche[parent_node][i].keys():
                    if 'id' in marche[parent_node][i][child_node]:
                        marche[parent_node][i][child_node]['id'] = int(marche[parent_node][i][child_node]['id'])
                    if 'montant' in marche[parent_node][i][child_node]:
                        marche[parent_node][i][child_node]['montant'] = float(marche[parent_node][i][child_node]['montant'])
                    if 'dureeMois' in marche[parent_node][i][child_node]:
                        marche[parent_node][i][child_node]['dureeMois'] = int(marche[parent_node][i][child_node]['dureeMois'])

