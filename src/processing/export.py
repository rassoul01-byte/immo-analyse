"""Écriture des résultats : données propres, quarantaine, journaux.

Les fichiers de data/raw/ ne sont jamais touchés ; tout est écrit dans
data/processed/, data/quarantine/ et reports/. Relancer le pipeline
remplace ces fichiers : le résultat est identique (idempotence).
"""
from pathlib import Path

import pandas as pd

from src.validation.doublons import DOUBLON_ECARTE, EXACT
from src.validation.moteur import AVEC_AVERTISSEMENT, CONFORME_TOTAL, QUARANTAINE
from src.validation.regle import AVERTISSEMENT, BLOQUANTE

COLONNES_PROPRES = [
    "id_bien", "source", "id_local", "date", "type_transaction", "type_bien",
    "region", "ville", "prix", "surface", "chambres", "salles_bain",
    "periodicite", "statut_annonce", "avertissements", "classement",
]


def _id_bien(source, id_local) -> str:
    return f"{source}:{id_local}"


def _regrouper(violations: pd.DataFrame, gravite: str, avec_motif: bool) -> dict:
    sous = violations[violations["gravite"] == gravite]
    resultat = {}
    for id_ligne, groupe in sous.groupby("id_ligne"):
        if avec_motif:
            resultat[id_ligne] = " | ".join(f"{c}: {m}" for c, m in zip(groupe["code"], groupe["motif"]))
        else:
            resultat[id_ligne] = "; ".join(groupe["code"])
    return resultat


def donnees_propres(classe: pd.DataFrame, violations: pd.DataFrame) -> pd.DataFrame:
    gardes = classe[classe["classement"].isin([CONFORME_TOTAL, AVEC_AVERTISSEMENT])].copy()
    gardes["id_bien"] = [_id_bien(s, i) for s, i in zip(gardes["source"], gardes["id_local"])]
    gardes["avertissements"] = gardes["id_ligne"].map(_regrouper(violations, AVERTISSEMENT, False)).fillna("")
    gardes["date"] = gardes["date"].map(lambda d: d.isoformat() if pd.notna(d) else None)
    for col in ("chambres", "salles_bain"):
        gardes[col] = gardes[col].astype("Int64")
    return gardes[COLONNES_PROPRES].reset_index(drop=True)


def donnees_quarantaine(df: pd.DataFrame, classe: pd.DataFrame,
                        violations: pd.DataFrame, liens: pd.DataFrame) -> pd.DataFrame:
    rejetes = classe[classe["classement"].isin([QUARANTAINE, DOUBLON_ECARTE])].copy()
    motifs = _regrouper(violations, BLOQUANTE, True)
    exacts = liens[liens["type_lien"] == EXACT]
    copies = {b: f"copie exacte de {s}:{i}" for b, s, i in
              zip(exacts["id_b"], exacts["source_a"], exacts["id_local_a"])}

    def motif(id_ligne):
        return copies.get(id_ligne) or motifs.get(id_ligne, "")

    rejetes["motifs"] = rejetes["id_ligne"].map(motif)
    brut = df[["date", "prix", "surface"]].add_prefix("brut_")
    rejetes = rejetes.join(brut, on="id_ligne")
    colonnes = ["id_ligne", "source", "id_local", "classement", "motifs",
                "brut_date", "brut_prix", "brut_surface"]
    return rejetes[colonnes].reset_index(drop=True)


def exporter_resultats(df, classe, violations, liens, journal, racine: Path) -> dict:
    processed = racine / "data" / "processed"
    quarantine = racine / "data" / "quarantine"
    reports = racine / "reports"
    for dossier in (processed, quarantine, reports):
        dossier.mkdir(parents=True, exist_ok=True)

    propres = donnees_propres(classe, violations)
    quarantaine = donnees_quarantaine(df, classe, violations, liens)

    propres.to_csv(processed / "biens_propres.csv", index=False, encoding="utf-8")
    propres.to_json(processed / "biens_propres.json", orient="records",
                    force_ascii=False, indent=2)
    quarantaine.to_csv(quarantine / "quarantaine.csv", index=False, encoding="utf-8")
    quarantaine.to_json(quarantine / "quarantaine.json", orient="records",
                        force_ascii=False, indent=2)
    journal.to_csv(reports / "journal_normalisation.csv", index=False, encoding="utf-8")
    violations.to_csv(reports / "violations.csv", index=False, encoding="utf-8")
    liens.to_csv(reports / "liens_doublons.csv", index=False, encoding="utf-8")
    return {"propres": len(propres), "quarantaine": len(quarantaine)}