import re

# Nom du fichier
filename = "tools_api/Log_Verification_DECP_.txt"

# Ensemble pour stocker des valeurs uniques
unique_values = set()

# Ouvrir le fichier en mode lecture
with open(filename, 'r') as file:
    for line in file:
        # Chercher les entiers uniques qui commencent par le préfixe
        matches = re.findall(r'\$\.marches\.marche\[(\d+)\]', line)
        
        # Ajouter les entiers trouvés à l'ensemble
        unique_values.update(matches)

# Convertir le set en liste et la trier
unique_values = sorted(unique_values)

# Afficher les valeurs uniques
print("Valeurs uniques :", unique_values)

# Afficher le nombre de valeurs uniques
print("Nombre de valeurs uniques :", len(unique_values))