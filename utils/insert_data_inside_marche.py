import json

def load_json(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return json.load(file)

def save_json(data, file_path):
    with open(file_path, 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=4)

def restructure_data(input_file, output_file):

    # Charger le fichier JSON en entrée
    data = load_json(input_file)
    
    # Créer un nouveau noeud 'marche' au dessus du noeud 'marches'
    new_structure = {
        'marches': {
            'marche': data.get('marches', [])
        }
    }

    # Sauvegarder le JSON obtenu dans le fichier 
    save_json(new_structure, output_file)

if __name__ == "__main__":
    input_file_path = 'results/decp-2022__REFERENCE.json'
    output_file_path = 'results/decp-2022.json'

    restructure_data(input_file_path, output_file_path)

    print(f"Le nœud 'marche' a été placé dans 'marches' et sauvegardé dans {output_file_path}.")