from src.loaders.excel_loader import charger_teranga, charger_teranga_params

df = charger_teranga()
print(df.shape, df["source"].iloc[0])
print(charger_teranga_params())