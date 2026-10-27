import pandas as pd

RAW = "data/raw/immoanalyse_dataset/sources"
h = pd.read_csv(f"{RAW}/import_historique.csv", sep=";", encoding="latin-1")

slash = h[h["DateVente"].str.contains("/", na=False)]["DateVente"]
parts = slash.str.split("/", expand=True).astype(int)

print("Premier nombre > 12 :", (parts[0] > 12).sum())
print("Second nombre > 12  :", (parts[1] > 12).sum())
print("Valeurs impossibles (jour>31 ou mois>12) :")
print(slash[(parts[0] > 31) | (parts[1] > 12) & (parts[0] <= 12)].tolist())