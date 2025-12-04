import shutil
import os
import subprocess
# script a executer depuis wsl dans le repertoire de base du projet decp-rama sous l'environnement virtuel


current_year = 2025
current_month = 10  # C'est juin 2025
date_prefix = '2025-12-04'

RESULT_PATH = "/mnt/c/projets/decp-rama/results/global"

data_dir = '/mnt/c/projets/decp-rama/data'  # Remplacez par le chemin correct
data_dir_dest = f'{data_dir}/GENERATED'  # Remplacez par le chemin correct

# Étape 1: Itération sur les années et les mois
for year in range(2024, current_year + 1):
    for month in range(1, 13):
        if year == current_year and month > current_month:
            break  # Sortir si on dépasse le mois actuel
        
        print(f"Launch decp-rama for {month}/{year}")
        # Étape 1: Copier decp-2024-01.json vers decp-daily.json
        new_date_prefix = f'{year}-{month:02}'

        source_file = f"{RESULT_PATH}/decp-global-{new_date_prefix}.json" 
        destination_file = '/mnt/c/projets/decp-rama/results/decp-daily.json'
        shutil.copy(source_file, destination_file)
        print(f"Copié {source_file} vers {destination_file}")

        # Étape 2: Appeler le script main.py
        subprocess.run(['python3.12', 'main.py', '-a', '-r', '-l'])
        print("Le script main.py a été appelé.")

        # Étape 3: Renommer les fichiers générés dans le répertoire data

        # Liste des fichiers à renommer et déplacer
        files_to_rename = [
            f"{data_dir}/{date_prefix}-marche-2022.csv",
            f"{data_dir}/{date_prefix}-marche-exclu-2022.csv",
            f"{data_dir}/{date_prefix}-concession-2022.csv",
            f"{data_dir}/{date_prefix}-concession-exclu-2022.csv"
        ]

        # Noms des nouveaux fichiers
        new_filenames = [
            f"{data_dir_dest}/marches-valides/{new_date_prefix}-marche-2022.csv",
            f"{data_dir_dest}/marches-invalides/{new_date_prefix}-marche-exclu-2022.csv",
            f"{data_dir_dest}/concessions-valides/{new_date_prefix}-concession-2022.csv",
            f"{data_dir_dest}/concessions-invalides/{new_date_prefix}-concession-exclu-2022.csv"
        ]

        # Renommer les fichiers
        for old_file, new_file in zip(files_to_rename, new_filenames):
            if os.path.exists(old_file):
                #os.rename(old_file, os.path.join(data_dir, new_file))
                shutil.move(old_file, new_file)
                print(f"Renommé {old_file} en {new_file}")
            else:
                print(f"Le fichier {old_file} n'existe pas.")
