import pandas as pd

RAW = "data/raw/immoanalyse_dataset/sources"

plateforme = pd.read_csv(f"{RAW}/plateforme_immo_sn.csv", sep=";")
historique = pd.read_csv(f"{RAW}/import_historique.csv", sep=";", encoding="latin-1")

# 1. Valeurs de texte qui ne se convertissent pas en nombre
for nom, df, col in [
    ("plateforme", plateforme, "prix"),
    ("plateforme", plateforme, "surface"),
    ("historique", historique, "Prix"),
    ("historique", historique, "Surface"),
]:
    brut = df[col].dropna().astype(str)
    converti = pd.to_numeric(brut, errors="coerce")
    echecs = brut[converti.isna()]
    print(f"\n{nom}.{col} : {len(echecs)} non convertibles sur {len(brut)}")
    print(echecs.head(15).tolist())

# 2. Variantes d'écriture des catégories
print("\n", plateforme["type_transaction"].value_counts(dropna=False))
print("\n", plateforme["categorie"].value_counts(dropna=False))
print("\n", historique["TypeBien"].value_counts(dropna=False))

# 3. Formats de dates : chaque chiffre est remplacé par 9
for nom, df, col in [("plateforme", plateforme, "date_mise_en_ligne"),
                     ("historique", historique, "DateVente")]:
    motifs = df[col].astype(str).str.replace(r"\d", "9", regex=True)
    print(f"\nFormats de dates {nom} :")
    print(motifs.value_counts().head(10))