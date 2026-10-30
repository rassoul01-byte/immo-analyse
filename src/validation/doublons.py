"""Détection des doublons et des conflits entre enregistrements (D-014).

Quatre types de liens entre deux enregistrements :
- doublon_exact       : même source, même identifiant, tous les champs métier identiques
- conflit_identifiant : même source, même identifiant, mais valeurs différentes
- doublon_probable    : même bien apparent (transaction, type, ville, surface, date, prix proches,
                        nombre de chambres compatible)
- conflit_prix        : même bien apparent, mais prix qui se contredisent

On ne fusionne jamais deux enregistrements : un doublon exact voit sa copie écartée,
tout le reste est signalé et conservé.
"""
from collections import defaultdict
from itertools import combinations

import pandas as pd

from src.config import CONFIG
from src.validation.moteur import AVEC_AVERTISSEMENT, CONFORME_TOTAL

TOLERANCES = CONFIG["doublons"]

EXACT = "doublon_exact"
CONFLIT_ID = "conflit_identifiant"
PROBABLE = "doublon_probable"
CONFLIT_PRIX = "conflit_prix"
DOUBLON_ECARTE = "doublon_ecarte"

CHAMPS_EXACTS = ["type_transaction", "type_bien", "region", "ville",
                 "prix", "surface", "chambres", "salles_bain", "date"]
CHAMPS_BLOC = ("type_transaction", "type_bien", "ville", "surface", "date")


def _egal(a, b) -> bool:
    if pd.isna(a) and pd.isna(b):
        return True
    if pd.isna(a) or pd.isna(b):
        return False
    return a == b


def _ecart_pct(a: float, b: float) -> float:
    plus_grand = max(abs(a), abs(b))
    return 0.0 if plus_grand == 0 else abs(a - b) / plus_grand * 100


def _chambres_incompatibles(a, b) -> bool:
    return pd.notna(a["chambres"]) and pd.notna(b["chambres"]) and a["chambres"] != b["chambres"]


def _lien(a, b, type_lien, motif) -> dict:
    return {"id_a": a["id_ligne"], "id_b": b["id_ligne"],
            "source_a": a["source"], "source_b": b["source"],
            "id_local_a": a["id_local"], "id_local_b": b["id_local"],
            "type_lien": type_lien, "motif": motif}


def detecter_doublons(df_norm: pd.DataFrame) -> pd.DataFrame:
    lignes = df_norm.to_dict("records")
    liens = []

    # 1. identifiants répétés dans une même source
    par_id = defaultdict(list)
    for r in lignes:
        if pd.notna(r["id_local"]):
            par_id[(r["source"], r["id_local"])].append(r)
    for rows in par_id.values():
        for a, b in combinations(rows, 2):
            if all(_egal(a[c], b[c]) for c in CHAMPS_EXACTS):
                liens.append(_lien(a, b, EXACT, "mêmes identifiant et valeurs"))
            else:
                diff = [c for c in CHAMPS_EXACTS if not _egal(a[c], b[c])]
                liens.append(_lien(a, b, CONFLIT_ID,
                                   "même identifiant, valeurs différentes : " + ", ".join(diff)))
    deja = {(l["id_a"], l["id_b"]) for l in liens}

    # 2. biens apparemment identiques (blocage par transaction, type et ville)
    blocs = defaultdict(list)
    for r in lignes:
        if all(pd.notna(r[c]) for c in CHAMPS_BLOC):
            blocs[(r["type_transaction"], r["type_bien"], r["ville"])].append(r)
    for rows in blocs.values():
        for a, b in combinations(rows, 2):
            if (a["id_ligne"], b["id_ligne"]) in deja:
                continue
            if _chambres_incompatibles(a, b):
                continue  # deux nombres de chambres connus et différents : biens distincts
            ecart_surface = _ecart_pct(a["surface"], b["surface"])
            jours = abs((a["date"] - b["date"]).days)
            if ecart_surface > TOLERANCES["tolerance_surface_pct"] or jours > TOLERANCES["tolerance_date_jours"]:
                continue
            if pd.isna(a["prix"]) or pd.isna(b["prix"]):
                continue  # sans prix, la preuve est insuffisante : on ne signale pas
            ecart_prix = _ecart_pct(a["prix"], b["prix"])
            detail = f"surface ±{ecart_surface:.1f} %, date ±{jours} j, prix ±{ecart_prix:.1f} %"
            if ecart_prix <= TOLERANCES["tolerance_prix_pct"]:
                liens.append(_lien(a, b, PROBABLE, detail))
            else:
                liens.append(_lien(a, b, CONFLIT_PRIX, detail))

    colonnes = ["id_a", "id_b", "source_a", "source_b", "id_local_a", "id_local_b",
                "type_lien", "motif"]
    return pd.DataFrame(liens, columns=colonnes)


def integrer_au_classement(classe: pd.DataFrame, liens: pd.DataFrame) -> pd.DataFrame:
    """Copies exactes écartées ; autres liens signalés (avertissement) sans fusion."""
    out = classe.copy()
    copies = set(liens.loc[liens["type_lien"] == EXACT, "id_b"])
    autres = liens[liens["type_lien"] != EXACT]
    signales = set(autres["id_a"]) | set(autres["id_b"])

    def nouveau(ligne):
        if ligne["id_ligne"] in copies:
            return DOUBLON_ECARTE
        if ligne["id_ligne"] in signales and ligne["classement"] == CONFORME_TOTAL:
            return AVEC_AVERTISSEMENT
        return ligne["classement"]

    out["classement"] = out.apply(nouveau, axis=1)
    return out
