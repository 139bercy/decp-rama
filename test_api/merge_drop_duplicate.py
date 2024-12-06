import io
import json
import pandas as pd

path = "results/decp-daily.json"
with open(path, encoding="utf-8") as f:
    dico1 = json.load(f)
print(f"dico1 lenght: {len(dico1['marches'])}")

with open(path, encoding="utf-8") as f:
    dico2 = json.load(f)
print(f"dico2 length: {len(dico2['marches'])}")

dico = dico1['marches'] + dico2['marches']
print(f"dico length: {len(dico)}")

df = pd.DataFrame.from_dict(dico)
print(f"df length: {df.size}")
print(f"df type: {type(df)}")

df_str  = df.astype(str)
            
feature_doublons_marche = ["id","acheteur", "titulaires", "dateNotification", "montant"] 

index_to_keep = df_str.drop_duplicates(subset=feature_doublons_marche).index.tolist()

df_dropped_duplicates = df.loc[index_to_keep, :]
print(f"df dropped lenght: {df_dropped_duplicates.size}")

dico_final = df_dropped_duplicates.to_dict(orient='records')
print(f"dico_final length: {len(dico_final)}")
