import json

# Load json file
def load_json(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return json.load(file)

# Save json file
def save_json(data, file_path):
    with open(file_path, 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=4)

# Merge json files
def merge_data(reference_file, month_data_file):

    # Load agreged data decp_2022.json
    reference_data = load_json(reference_file)
    
    # Load month data
    month_data = load_json(month_data_file)
    
    # Vérifier que le noeud 'marches' existe dans les données 2022
    if 'marches' not in reference_data:
        reference_data['marches'] = []

    # Merge month data decp_8.json into decp_2022.json
    reference_data['marches'].extend(month_data['marches'])

    # Save data
    save_json(reference_data, reference_file)

if __name__ == "__main__":
    reference_file_path = 'results/decp-2022.json'
    month_data_file = 'results/decp-2024-9.json'

    merge_data(reference_file_path, month_data_file)

    print(f"Les données de {month_data_file}ont été fusionnées dans {reference_file_path}.")
