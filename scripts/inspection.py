import pandas as pd

RAW = "data/raw/immoanalyse_dataset/sources"

plateforme = pd.read_csv(f"{RAW}/plateforme_immo_sn.csv", sep=";")
historique = pd.read_csv(f"{RAW}/import_historique.csv", sep=";", encoding="latin-1")
notaires   = pd.read_csv(f"{RAW}/notaires.csv", sep=",")

for nom, df in [("plateforme", plateforme), ("historique", historique), ("notaires", notaires)]:
    print(f"\n=== {nom} : {df.shape}")
    print(df.dtypes)
    print(df.isna().sum())
    