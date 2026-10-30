"""Point d'entrée du pipeline ImmoAnalyse.

Lancer depuis la racine du projet :
    python -m src.main
    python -m src.main --date 2026-10-29     # date d'exécution fixée (reproductibilité)
"""
import argparse
from datetime import date
from pathlib import Path

from src.analysis.rapport_qualite import construire_rapport, ecrire_rapport
from src.config import RACINE
from src.loaders.harmonisation import charger_toutes_les_sources
from src.processing.export import exporter_resultats
from src.processing.normaliser_df import normaliser_dataframe
from src.validation.doublons import detecter_doublons, integrer_au_classement
from src.validation.moteur import appliquer_regles, classer
from src.validation.regles_metier import construire_regles


def executer(date_execution: date, racine: Path = RACINE) -> dict:
    df = charger_toutes_les_sources()
    df_norm, journal = normaliser_dataframe(df)
    violations, regles = appliquer_regles(df_norm, construire_regles(date_execution))
    liens = detecter_doublons(df_norm)
    classe = integrer_au_classement(classer(df_norm, violations), liens)

    exporter_resultats(df, classe, violations, liens, journal, racine)
    rapport = construire_rapport(df, df_norm, classe, journal, regles, liens, date_execution)
    ecrire_rapport(rapport, racine / "reports")
    return rapport


def main(argv=None) -> None:
    parseur = argparse.ArgumentParser(description="Pipeline ImmoAnalyse")
    parseur.add_argument("--date", help="date d'exécution AAAA-MM-JJ (défaut : aujourd'hui)")
    args = parseur.parse_args(argv)
    date_execution = date.fromisoformat(args.date) if args.date else date.today()

    rapport = executer(date_execution)
    e = rapport["enregistrements"]
    print(f"Date d'exécution : {rapport['date_execution']}")
    print(f"Enregistrements reçus : {rapport['total_recus']}")
    print(f"  entièrement conformes : {e['entierement_conformes']}")
    print(f"  conservés avec avertissement : {e['conserves_avec_avertissement']}")
    print(f"  mis en quarantaine : {e['quarantaine']}")
    print(f"  doublons écartés : {e['doublons_ecartes']}")
    print(f"Taux global entièrement conformes : {rapport['taux_global_entierement_conformes_pct']} %")
    print("Résultats : data/processed/, data/quarantine/, reports/")


if __name__ == "__main__":
    main()