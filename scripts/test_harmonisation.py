from src.loaders.harmonisation import charger_toutes_les_sources

df = charger_toutes_les_sources()
print(df.shape)
print(df["source"].value_counts())
print(df.isna().sum())