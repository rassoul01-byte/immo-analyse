"""Applique les normalisations à un DataFrame harmonisé.

Renvoie (df_norm, journal) :
- df_norm : une ligne par enregistrement, valeurs normalisées + colonnes <champ>_statut
- journal : une ligne par anomalie ou correction (valeur brute, valeur normalisée, motif)
"""
import re

import pandas as pd

from src.config import CONFIG
from src.processing.normalisation import (
    CORRIGE, INVALIDE, MANQUANT, OK, Resultat, est_vide,
    normaliser_date, normaliser_prix, normaliser_region, normaliser_surface,
    normaliser_type_bien, normaliser_ville,
)
from src.processing.transaction import deduire_type_transaction

# Colonnes qui n'existent pas dans la source : non évaluables, pas « manquantes »
ABSENTS_PAR_CONSTRUCTION = {("plateforme", "chambres"), ("notaires", "salles_bain")}


def normaliser_entier(brut) -> Resultat:
    if est_vide(brut):
        return Resultat(None, MANQUANT, "valeur absente")
    texte = str(brut).strip()
    if re.fullmatch(r"\d+(?:\.0+)?", texte):
        return Resultat(int(float(texte)), OK, "")
    return Resultat(None, INVALIDE, f"entier >= 0 attendu : {brut!r}")


def deduire_periodicite(devise) -> Resultat:
    """Périodicité lue dans la devise (« FCFA/mois »). Jamais devinée."""
    if est_vide(devise):
        return Resultat(None, MANQUANT, "périodicité non fournie")
    texte = str(devise).strip().lower()
    for marqueur, valeur in CONFIG["synonymes_periodicite"].items():
        if marqueur in texte:
            return Resultat(valeur, CORRIGE, f"lue dans la devise {devise!r}")
    return Resultat(None, MANQUANT, "périodicité non fournie")


def normaliser_dataframe(df: pd.DataFrame):
    lignes, journal = [], []

    def noter(i, source, champ, brut, res):
        if res.statut == OK:
            return
        if res.statut == MANQUANT and (source, champ) in ABSENTS_PAR_CONSTRUCTION:
            return
        if champ == "periodicite" and res.statut == MANQUANT:
            return  # absente des ventes par nature ; signalée par la règle A08
        journal.append({"id_ligne": i, "source": source, "champ": champ,
                        "valeur_brute": brut, "valeur_normalisee": res.valeur,
                        "statut": res.statut, "motif": res.motif})

    for i, r in enumerate(df.to_dict("records")):
        source = r["source"]
        res = {
            "date": normaliser_date(r["date"], jour_en_premier=True),
            "prix": normaliser_prix(r["prix"]),
            "surface": normaliser_surface(r["surface"]),
            "type_bien": normaliser_type_bien(r["type_bien"]),
            "region": normaliser_region(r["region"]),
            "ville": normaliser_ville(r["ville"]),
            "chambres": normaliser_entier(r["chambres"]),
            "salles_bain": normaliser_entier(r["salles_bain"]),
        }
        res["type_transaction"] = deduire_type_transaction(
            source, r["type_transaction"], r["statut"], res["prix"].valeur)
        res["periodicite"] = deduire_periodicite(r["devise"])

        ligne = {"id_ligne": i, "source": source,
                 "id_local": None if est_vide(r["id_local"]) else str(r["id_local"]).strip(),
                 "statut_annonce": None if est_vide(r["statut"]) else r["statut"]}
        for champ, resultat in res.items():
            ligne[champ] = resultat.valeur
            ligne[f"{champ}_statut"] = resultat.statut
            brut = r["devise"] if champ == "periodicite" else r.get(champ)
            noter(i, source, champ, brut, resultat)
        lignes.append(ligne)

    return pd.DataFrame(lignes), pd.DataFrame(journal)
