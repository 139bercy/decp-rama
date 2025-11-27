import re

# Chargement du contenu XML depuis le fichier <>.xml
with open('test_api/decp-13000495500139-2024-10-10-06.xml', 'r', encoding='utf-8') as file:
    xml_content = file.read()

# Expression régulière pour trouver toutes les balises contenant "NC"
pattern = r'<[^>]*>NC<\/[^>]*>'

# Trouver toutes les correspondances
matches = re.findall(pattern, xml_content)

# Supprimer les doublons
unique_matches = set(matches)

# Afficher les résultats
for match in unique_matches:
    print(match)

print('end')