import os
import boto3
import json
from zipfile import ZipFile
from saagieapi import SaagieApi

# Credentials en provenance de la CI
ACCESS_KEY = os.environ.get("ACCESS_KEY")
SECRET_KEY = os.environ.get("SECRET_KEY")
USER_SAAGIE =os.environ.get("USER_SAAGIE")
PASSWORD = os.environ.get("PASSWORD_SAAGIE")
ENDPOINT_S3 = os.environ.get("ENDPOINT_S3")
PROJECT_NAME = os.environ.get("PROJECT_NAME")
BUCKET_NAME = os.environ.get("BUCKET_NAME") 
JOB_NAME = "decp_rama_v2"
ZIP_NAME = "decp_rama_v2.zip"


def main():
    files_to_add = []
    specific_path = "specific_process"
    for file in os.listdir(specific_path): # On ajoute tous les fichiers de specific process
        files_to_add.append(os.path.join(specific_path, file))
    # De même avec les general_process
    general_path = "general_process"
    for file in os.listdir(general_path):
        files_to_add.append(os.path.join(general_path, file))
    # Puis metadata
    files_to_add.append("metadata/metadata.json")
    # Puis main.py
    files_to_add.append("main.py")
    # le fichier de config
    files_to_add.append("config.json")
    # Et finalement les requirements
    files_to_add.append("requirements.txt")

    # Maintenant, on zip tout ces fichiers
    zipObj = ZipFile(ZIP_NAME, "w")
    for file in files_to_add:
        zipObj.write(file)
    zipObj.close()

    saagieapi =  SaagieApi.easy_connect(url_saagie_platform="https://mefsin-workspace.pcv.saagie.io/projects/platform/1/project/4fbca8d8-b3a5-4f63-97f1-b2ca6362a2b2/jobs",
        user=USER_SAAGIE,
        password=PASSWORD)
    try:
        id_job = saagieapi.jobs.get_id(project_name=PROJECT_NAME, job_name=JOB_NAME)
        saagieapi.jobs.upgrade(job_id=id_job, file=ZIP_NAME, command_line="python3 main.py", runtime_version='3.9')
        print('Job upgrade')
    except Exception:
        print(f"{Exception}, Le jobs {JOB_NAME} n existe pas. On le créé")
        id_projet = saagieapi.projects.get_id(PROJECT_NAME)
        saagieapi.jobs.create(job_name=JOB_NAME, file=ZIP_NAME, command_line="python3 main.py", project_id=id_projet,
        category='Extraction',
        technology='python',  # technology id corresponding to your context.id in your technology catalog definition
        technology_catalog='Saagie',
        runtime_version='3.9')


if __name__ == "__main__":
    main()
