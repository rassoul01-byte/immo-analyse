"""Rapport de qualité chiffré : reports/quality_report.json et quality_summary.csv."""
import json
from datetime import date
from pathlib import Path

import pandas as pd

from src.processing.normalisation import AMBIGU, CORRIGE, INVALIDE, est_vide
from src.validation.doublons import CONFLIT_ID, CONFLIT_PRIX, EXACT, PROBABLE

# Champs dérivés (déduits, pas corrigés) : comptés à part des corrections
CHAMPS_DERIVES = {"type_transaction", "periodicite"}


def _manquantes(df: pd.DataFrame) -> dict:
    resultat = {}
    for colonne in [c for c in df.columns if c != "source"]:
        vides = df[colonne].map(est_vide)
        resultat[colonne] = {
            "total": int(vides.sum()),
            "taux_pct": round(100 * vides.mean(), 2),
            "par_source": {s: int(v) for s, v in vides.groupby(df["source"]).sum().items()},
        }
    return resultat


def _absentes_par_construction(df: pd.DataFrame) -> list:
    """Colonnes entièrement vides dans une source : non fournies, donc non évaluables."""
    absentes = []
    for source, groupe in df.groupby("source"):
        for colonne in [c for c in df.columns if c != "source"]:
            if groupe[colonne].map(est_vide).all():
                absentes.append(f"{source}.{colonne}")
    return absentes


def construire_rapport(df, df_norm, classe, journal, regles, liens, date_execution: date) -> dict:
    total = len(df)
    nb_exacts = int((liens["type_lien"] == EXACT).sum())
    classement = classe["classement"].value_counts().to_dict()

    erreurs = journal[journal["statut"].isin([INVALIDE, AMBIGU])].groupby("champ").size()
    corriges = journal[(journal["statut"] == CORRIGE) & ~journal["champ"].isin(CHAMPS_DERIVES)]
    deduits = journal[(journal["statut"] == CORRIGE) & (journal["champ"] == "type_transaction")]

    entierement = classement.get("entierement_conforme", 0)
    return {
        "date_execution": date_execution.isoformat(),
        "total_recus": total,
        "recus_par_source": df["source"].value_counts().to_dict(),
        "valeurs_manquantes": _manquantes(df),
        "colonnes_absentes_par_construction": _absentes_par_construction(df),
        "doublons": {
            "exacts": nb_exacts,
            "taux_exacts_pct": round(100 * nb_exacts / total, 2),
            "probables": int((liens["type_lien"] == PROBABLE).sum()),
            "conflits_identifiant": int((liens["type_lien"] == CONFLIT_ID).sum()),
            "conflits_prix": int((liens["type_lien"] == CONFLIT_PRIX).sum()),
        },
        "erreurs_conversion_par_champ": {k: int(v) for k, v in erreurs.items()},
        "regles": regles.to_dict("records"),
        "enregistrements": {
            "corriges": int(corriges["id_ligne"].nunique()),
            "type_transaction_deduit": int(deduits["id_ligne"].nunique()),
            "quarantaine": classement.get("quarantaine", 0),
            "conserves_avec_avertissement": classement.get("conserve_avec_avertissement", 0),
            "entierement_conformes": entierement,
            "doublons_ecartes": classement.get("doublon_ecarte", 0),
        },
        "taux_global_entierement_conformes_pct": round(100 * entierement / total, 2),
        "definitions": {
            "taux_conformite_regle": "conformes / evaluables x 100 ; les non evaluables sont comptes a part",
            "classement": "chaque enregistrement est compte une seule fois : doublon ecarte, sinon quarantaine "
                          "(au moins une regle bloquante violee), sinon avertissement, sinon entierement conforme",
            "taux_global": "entierement conformes / total recus",
            "corriges": "enregistrements ayant au moins une valeur normalisee (hors type de transaction et periodicite deduits)",
        },
        "limites": [
            "Seuils de plausibilite : hypotheses pedagogiques, pas des normes de marche.",
            "Donnees synthetiques : aucune conclusion sur les prix reels du marche.",
            "Aucun doublon probable detecte entre sources avec les criteres retenus (voir D-014).",
            "La regle B06 depend de la date d'execution.",
        ],
    }


def ecrire_rapport(rapport: dict, dossier: Path) -> None:
    dossier.mkdir(parents=True, exist_ok=True)
    with open(dossier / "quality_report.json", "w", encoding="utf-8") as f:
        json.dump(rapport, f, ensure_ascii=False, indent=2)

    lignes = [("total_recus", rapport["total_recus"])]
    lignes += [(f"recus.{s}", n) for s, n in rapport["recus_par_source"].items()]
    lignes += [(f"manquantes.{c}", v["total"]) for c, v in rapport["valeurs_manquantes"].items()]
    lignes += [(f"doublons.{k}", v) for k, v in rapport["doublons"].items()]
    lignes += [(f"erreurs_conversion.{k}", v) for k, v in rapport["erreurs_conversion_par_champ"].items()]
    for r in rapport["regles"]:
        lignes.append((f"regle.{r['code']}.taux_conformite_pct", r["taux_conformite"]))
        lignes.append((f"regle.{r['code']}.denominateur_evaluables", r["evaluables"]))
        lignes.append((f"regle.{r['code']}.non_evaluables", r["non_evaluables"]))
    lignes += [(f"enregistrements.{k}", v) for k, v in rapport["enregistrements"].items()]
    lignes.append(("taux_global_entierement_conformes_pct",
                   rapport["taux_global_entierement_conformes_pct"]))
    pd.DataFrame(lignes, columns=["indicateur", "valeur"]).to_csv(
        dossier / "quality_summary.csv", index=False, encoding="utf-8")