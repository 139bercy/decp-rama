from enum import Enum
import json 

class Step (Enum):
    NONE = 0
    GET = 1
    CLEAN = 2
    CONVERT = 3
    FIX = 4
    MERGED = 5
    MERGE_ALL = 6
    FIX_ALL = 7
    DUPLICATE = 8
    GLOBAL = 9
    EXPORT = 10
    UPLOAD_DATA_GOUV = 10
    AUGMENTE_LOAD = 11
    AUGMENTE_CLEAN = 12
    UPLOAD_DATA_ECO = 13
    

if __name__ == '__main__':

    # Créer un dictionnaire avec l'attribut 'source'
    data_to_save = {
        "source": Step.CLEAN.value  # Utiliser la valeur de l'énumération
    }

    # Sauvegarder le dictionnaire dans un fichier JSON
    with open('data.json', 'w') as json_file:
        json.dump(data_to_save, json_file)

    # Charger les données depuis le fichier JSON
    with open('data.json', 'r') as json_file:
        loaded_data = json.load(json_file)

    # Récupérer la valeur de l'attribut 'source'
    source_value = loaded_data['source']
    
    # Convertir la valeur chargée en membre de l'énumération
    source_enum = Step(source_value)
    