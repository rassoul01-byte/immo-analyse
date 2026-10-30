import pandas as pd

from src.analysis.statistiques import (
    charger_propres, loyers_mensuels, resume_loyers_par, resume_ventes_par,
    statistiques, ventes,
)
from src.config import RACINE

pd.set_option("display.width", 250)
pd.set_option("display.max_columns", None)
pd.set_option("display.float_format", lambda x: f"{x:,.0f}")

sortie = RACINE / "reports" / "analyses"
sortie.mkdir(parents=True, exist_ok=True)

df = charger_propres(RACINE / "data" / "processed" / "biens_propres.csv")
v = ventes(df)
l = loyers_mensuels(df)

print(f"Biens propres : {len(df)} | ventes exploitables : {len(v)} | "
      f"locations : {(df['type_transaction'] == 'location').sum()} dont loyers mensuels : {len(l)}")

stats = pd.DataFrame({"prix_vente": statistiques(v["prix"]),
                      "prix_m2": statistiques(v["prix_m2"]),
                      "surface": statistiques(v["surface"])})
print("\nStatistiques descriptives (ventes)\n", stats)

par_type = resume_ventes_par(v, "type_bien")
par_ville = resume_ventes_par(v, "ville")
loyers_type = resume_loyers_par(l, "type_bien")
print("\nVentes par type de bien\n", par_type)
print("\nVentes par ville (10 plus fournies)\n", par_ville.head(10))
print("\nLoyers mensuels par type de bien\n", loyers_type)

stats.to_csv(sortie / "statistiques_ventes.csv")
par_type.to_csv(sortie / "ventes_par_type.csv", index=False)
par_ville.to_csv(sortie / "ventes_par_ville.csv", index=False)
loyers_type.to_csv(sortie / "loyers_par_type.csv", index=False)