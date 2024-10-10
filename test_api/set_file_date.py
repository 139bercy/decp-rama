
import os
import datetime
import time

def modifier_date_fichier(nom_fichier, nouvelle_date):
    try:
        # Conversion de la nouvelle date au format timestamp
        date_objet = datetime.datetime.strptime(nouvelle_date, '%Y-%m-%d')
        timestamp = time.mktime(date_objet.timetuple())
        
        # Mise à jour de la date d'accès et de modification
        os.utime(nom_fichier, (timestamp, timestamp))
        
        print(f"La date du fichier '{nom_fichier}' a été mise à jour à {nouvelle_date}.")
    except FileNotFoundError:
        print(f"Erreur : le fichier '{nom_fichier}' n'existe pas.")
    except Exception as e:
        print(f"Une erreur est survenue : {e}")

# Spécifiez le chemin de votre fichier
nom_fichier = 'old_metadata/e-marchespublics/old_metadata_emar_0.json'
nouvelle_date = '2024-08-31'

modifier_date_fichier(nom_fichier, nouvelle_date)

