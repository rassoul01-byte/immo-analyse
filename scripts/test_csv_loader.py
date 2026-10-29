from src.loaders.csv_loader import charger_plateforme, charger_historique, charger_notaires

for f in (charger_plateforme, charger_historique, charger_notaires):
    df = f()
    print(f.__name__, df.shape, df["source"].iloc[0])