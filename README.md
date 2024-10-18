# decp-rama-v2
Decp-rama-v2 a pour objectif de recoder decp-rama (https://github.com/139bercy/decp-rama) en langage Python. Il s'agit encore d'un projet et le code présenté n'est donc pas celui aujourd'hui utilisé lors de la publication de base de données sur data.gouv.

Rappel de ce que sont les données essentielles de la commande publique (ou DECP) sur [le blog de data.gouv.fr](https://www.data.gouv.fr/fr/posts/le-point-sur-les-donnees-essentielles-de-la-commande-publique/).

L'objectif de ce projet est d'identifier toutes les sources de DECP, les aggréger afin de les publier (**[jeu de données sur data.gouv.fr](https://www.data.gouv.fr/fr/datasets/5cd57bf68b4c4179299eb0e9)**) aux formats JSON et XML réglementaires.

La procédure standard est la suivante pour chaque source de données :

### **1. ETAPE GET**

Nous téléchargeons les données d'une source dans son format d'origine, XML ou JSON (les DECP n'existent pas dans d'autres formats) dans le dossier /sources dans un répertoire spécifique à la source des données.

### **2. ETAPE CONVERT**

Nous convertissons par la suite en DataFrame afin de faire les opérations de nettoyage et d'aggrégation.

### **3. ETAPE FIX**

Certaines données sources n'étant pas valides, nous corrigeons ce qui peut être corrigé (par exemple le format d'une date). Si certains champs manquent dans les données, nous avons pris le parti de les garder et de signaler ces anomalies. On supprime également les lignes dupliquées (marchés présents plusieurs fois dans la source de données).

### **4. ETAPE GLOBAL**

- **merge_all :** On agrège les DataFrame en un DataFrame unique
- **drop_duplicate :** On supprime les lignes dupliquées (marchés présents dans plusieurs sources de données)
- **export_to_xml :** On exporte au format XML réglementaire
- **export_to_json :** On exporte au format JSON réglementaire

### **5. CONTINUOUS INTEGRATION**

Dans l'objectif de remplacement de decp-rama, decp-rama-v2 dispose d'une CI qui permet de publier automatiquement le résultat de son script de manière journalière. Tous les jours, la CI va :
- Lancer un docker via Github Action qui s'appuie sur une image publiée sur DockerHub. Cette image est générée via le DockerFile dans le dossier docker/
et publiée grâce au script publish_docker.sh
- Récuperer le dossier github via actions/checkout@v2
- Installer les dépendances nécessaires aux scripts de decp-rama-v2
- Lancer main.py
- Publier sur le serveur FTP de data.economie.gouv dans le dossier decp/test le résultat du script : results/decp.json

## **INSTRUCTIONS POUR FAIRE TOURNER EN LOCAL**

Pour faire tourner en local decp-rama-v2 et obtenir le fichier decp.json aggrégé directement sur votre machine il faut :
- Installer les dépendances présentes dans requirements.txt
- Disposer d'une connexion Internet satisfaisante
- Lancer ```python main.py``` dans le dossier principal
- Le fichier final decp.json se trouvera dans le fichier resultats/

Possibilité de lancer un seul process pour les tests : ```python main.py -P [process_name]```

## **FIX A EFFECTUER ET PISTES D'AMÉLIORATION**

Pour terminer le projet decp-rama-v2 et continuer à l'améliorer, voici les différents problèmes et sources d'améliorations :
- La source BFC n'est plus traitée du fait d'erreurs dans la manière de récupérer les URL à get
- Il faudrait prendre en compte que les drops duplicate inter-sources suppriment les deuxièmes lignes et font donc un "choix" de source arbitraire. Peut-être qu'un .agg serait propice afin de garder l'information. Où supprimer la colonne source lors de la publication
- La partie qui est la plus consommatrice de performance aujourd'hui est le téléchargement des données. Il faudrait mettre en place un système de cache des fichiers qui ne sont plus mis à jour afin de gagner en temps d'exécution. Le fichier global de stock pourrait être retéléchargé tous les mois puis mis à jour tous les jours via la publication d'un fichier journalier par exemple.
- Mettre en place la publication des données qui sont aujourd'hui uniquement publiées sur le serveur ftp de data.eco

Si vous avez connaissance de données essentielles de la commande publique facilement accessibles (téléchargement en masse possible) et qui ne sont pas encore identifiées dans le fichier metadata.json, merci de [nous en informer](#contact).
## Tableau des sources URL qui focntionnent ou non 
| Source          | URL                                                                                                                                                                                                                                                                                           	  			 | Status    |
|-----------------|:------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------:|-----------|
| marches-publics.info |                                                                                                                                             https://www.data.gouv.fr/fr/datasets/5cdb1722634f41416ffe90e2/                                                                                                                                             | OK        |
| decp_aws        |                                                                                                                   https://data.economie.gouv.fr/api/v2/catalog/datasets/decp_aws/exports/json?limit=-1&offset=0&timezone=UTC&apikey=                                                                                                                   | OK        |
| data.gouv.fr_aife |                                                                                                                                https://www.data.gouv.fr/fr/organizations/agence-pour-linformatique-financiere-de-letat/                                                                                                                                | OK        |
| e-marchespublics |                                                                                                                                             https://www.data.gouv.fr/fr/datasets/5c0a7845634f4139b2ee8883                                                                                                                                              | OK        |
| grandlyon       |                                                                                                                                  https://download.data.grandlyon.com/files/grandlyon/citoyennete/marches_publics.xml                                                                                                                                   | OK        |
| atexo-maximilien |                                                                                                                                               https://www.data.gouv.fr/datasets/5f4d1921f7e627ef3ae26944                                                                                                                                               | OK        |
| ternum-bfc      |                                                                                                                                                        http://focus-marches.ternum-bfc.fr/xml/                                                                                                                                                         | OK        |
| megalis-bretagne |                                                                                                                                             https://www.data.gouv.fr/fr/datasets/5f4f4f8910f4b55843deae51                                                                                                                                              | OK        |
| region-bretagne |                                                                                                                        https://data.bretagne.bzh/api/datasets/1.0/decp-crb/alternative_exports/decp2021_regionbretagne_csv_xml                                                                                                                         | OK        |
| data.gouv.fr_pes|                                                                                                                                             https://files.data.gouv.fr/decp/dgfip-pes-decp.xml                                                                                                                                              | ** KO **  |