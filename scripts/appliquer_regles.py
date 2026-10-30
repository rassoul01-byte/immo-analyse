from datetime import date

import pandas as pd

from src.loaders.harmonisation import charger_toutes_les_sources
from src.processing.normaliser_df import normaliser_dataframe
from src.validation.doublons import detecter_doublons, integrer_au_classement
from src.validation.moteur import appliquer_regles, classer
from src.validation.regles_metier import construire_regles

pd.set_option("display.width", 220)

date_execution = date.today()
df = charger_toutes_les_sources()
df_norm, journal = normaliser_dataframe(df)
violations, rapport = appliquer_regles(df_norm, construire_regles(date_execution))
liens = detecter_doublons(df_norm)
classe = integrer_au_classement(classer(df_norm, violations), liens)

print("Date d'exécution :", date_execution)
print("Journal de normalisation :", len(journal), "lignes\n")
print(rapport.to_string(index=False))
print("\nLiens entre enregistrements :")
print(liens["type_lien"].value_counts().to_string() if len(liens) else "aucun")
print("\n", classe["classement"].value_counts())
print("\n", classe.groupby(["source", "classement"]).size().unstack(fill_value=0))

taux_global = 100 * (classe["classement"] == "entierement_conforme").mean()
nb_exacts = int((liens["type_lien"] == "doublon_exact").sum())
print(f"\nDoublons exacts : {nb_exacts} ({100 * nb_exacts / len(df_norm):.2f} % de {len(df_norm)})")
print(f"Taux global d'enregistrements entièrement conformes : {taux_global:.2f} %")

rapport.to_csv("reports/regles_conformite.csv", index=False)
liens.to_csv("reports/liens_doublons.csv", index=False)
