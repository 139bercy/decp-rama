import json

with open('data/global/decp-global.json','r', encoding='utf-8') as fh:
    data = json.load(fh)

print(len(data['marches']['marche']))