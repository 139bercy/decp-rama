import pandas as pd
import numpy as np

data = {
    'id': [1, np.nan, pd.NA, 4, 5, '<NA>'],
    'montant': [100, np.nan, 300, None, pd.NA, 600],
    'Erreurs': [None] * 6
}
df = pd.DataFrame(data)

# Masque pour les ids vides
mask_id_vide = df['id'].isna() | (df['id'] == '<NA>')
df.loc[mask_id_vide, 'Erreurs'] = 'Colonne id vide'

# Masque pour les montants vides
mask_montant_vide = df['montant'].isna() | (df['montant'] == '<NA>')
# Concaténation sans multiplication de string par un booléen
df.loc[mask_montant_vide, 'Erreurs'] = (
    df.loc[mask_montant_vide, 'Erreurs'].fillna('') +
    (df.loc[mask_montant_vide, 'Erreurs'].notna().map(lambda x: '; ' if x else '')) +
    'Colonne montant vide'
)
# Remplacement des débuts de chaîne incorrects (évite "; Colonne montant vide" au début)
df['Erreurs'] = df['Erreurs'].str.lstrip('; ').replace('', np.nan)

print(df)
