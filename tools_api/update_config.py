from datetime import datetime
import io
import json

config_file = "config.json"
with open(config_file, "r") as file:
    data = json.load(file)

data['resource_id_global'] = None
data['resource_year'] = datetime.now().year

with open(config_file, "w") as file:
        json.dump(data, file, indent=4)
