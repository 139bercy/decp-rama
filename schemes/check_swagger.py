import json

# Load the swagger file and the schema file
swagger_file_path = 'schemes/swagger-decp-api_v1.0.2.json'
schema_file_path = 'schemes/schema_decp_v2.0.4.json'

with open(swagger_file_path, 'r') as file:
    swagger_data = json.load(file)

with open(schema_file_path, 'r') as file:
    schema_data = json.load(file)

# Check the structure of both files
swagger_data_keys = swagger_data.keys()
schema_data_keys = schema_data.keys()

swagger_data_keys, schema_data_keys
