from datetime import date

import pandas as pd

from src.loaders.harmonisation import charger_toutes_les_sources
from src.processing.normaliser_df import normaliser_dataframe
from src.validation.moteur import appliquer_regles, classer
from src.validation.regles_metier import construire_regles

pd.set_option("display.width", 220)

date_execution = date.today()
df = charger_toutes_les_sources()
df_norm, journal = normaliser_dataframe(df)
violations, rapport = appliquer_regles(df_norm, construire_regles(date_execution))
classe = classer(df_norm, violations)

print("Date d'exécution :", date_execution)
print("Journal de normalisation :", len(journal), "lignes\n")
print(rapport.to_string(index=False))
print("\n", classe["classement"].value_counts())
print("\n", classe.groupby(["source", "classement"]).size().unstack(fill_value=0))

taux_global = 100 * (classe["classement"] == "entierement_conforme").mean()
print(f"\nTaux global d'enregistrements entièrement conformes : {taux_global:.2f} %")

rapport.to_csv("reports/regles_conformite.csv", index=False)
