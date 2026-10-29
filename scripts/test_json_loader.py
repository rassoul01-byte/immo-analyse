from src.loaders.json_loader import charger_particuliers

df = charger_particuliers()
print(df.shape)
print(df.columns.tolist())
print(df.isna().sum())
print(df.head(3).T)