import json
import logging
import requests


def upload_file(headers,api,dataset_id,resource_id:str,suffix:str) -> str:
    if resource_id is None:
        url = f"{api}/datasets/{dataset_id}/upload/"
    else:
        url = f"{api}/datasets/{dataset_id}/resources/{resource_id}/upload/"
    
    try:
        # On charge le fichier annuel existant
        file = {
            "file": (f"decp-{suffix}.json", open(f"results/decp-{suffix}.json", "rb"))
        }
    except Exception:
        file = {
            "file": (f"decp-{suffix}.json", None)
        }

    response = requests.post(url, headers=headers, files=file)
    if response.status_code==200:
        logging.info(f"Upload du fichier decp-{suffix} réussi")
    elif response.status_code==201:
            logging.info(f"Création du fichier decp-{suffix}.json réussie")
            data = response.json()
            resource_id = data['id']
    else:
        logging.error(f'Error uploading file decp-{suffix}.json3')
    
    return resource_id

if __name__ == '__main__':
    config_file = "config.json"
    # read info from config.son
    with open(config_file, "r") as f:
            config = json.load(f)
            api = config["url_api"]
            dataset_id = config["dataset_id"]
            data_gouv_api_key = config["data_gouv_api_key"]

    headers = {
        "X-API-KEY": data_gouv_api_key
    }
    upload_file(headers,api,dataset_id,'398e075e-5dc2-4797-86d7-21d04e39111f','2024-11')
