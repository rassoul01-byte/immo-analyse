"""Fonctions de normalisation.

Chaque fonction renvoie un Resultat (valeur, statut, motif) :
- ok               : valeur déjà conforme, rien à corriger
- corrige          : valeur corrigée de façon fiable (le motif dit comment)
- manquant         : valeur absente ou marqueur vide
- invalide         : valeur inexploitable (non numérique, <= 0, date impossible)
- ambigu           : plusieurs lectures possibles, on ne devine pas
- hors_referentiel : valeur propre mais absente du référentiel
La gravité (quarantaine ou avertissement) est décidée plus tard, par les règles.
"""
import re
import unicodedata
from dataclasses import dataclass
from datetime import date
from functools import lru_cache
from typing import Any, Optional

import pandas as pd

from src.config import CHEMIN_REFERENTIEL_GEO, CONFIG

OK = "ok"
CORRIGE = "corrige"
MANQUANT = "manquant"
INVALIDE = "invalide"
AMBIGU = "ambigu"
HORS_REFERENTIEL = "hors_referentiel"

VALEURS_VIDES = set(CONFIG["valeurs_vides"])
UNITES = r"(?:fcfa|f\s*cfa|cfa)"
NOMBRES_EN_LETTRES = {"quatre-vingt": 80}
MOIS_FR = {
    "janvier": 1, "fevrier": 2, "mars": 3, "avril": 4, "mai": 5, "juin": 6,
    "juillet": 7, "aout": 8, "septembre": 9, "octobre": 10, "novembre": 11,
    "decembre": 12,
}


@dataclass(frozen=True)
class Resultat:
    valeur: Any
    statut: str
    motif: str = ""


# ---------- utilitaires ----------

def est_vide(valeur) -> bool:
    if not isinstance(valeur, str) and pd.isna(valeur):
        return True
    return str(valeur).strip().lower() in VALEURS_VIDES


def sans_accents(texte: str) -> str:
    decompose = unicodedata.normalize("NFKD", texte)
    return "".join(c for c in decompose if not unicodedata.combining(c))


def _nettoyer(brut) -> str:
    return str(brut).replace("\u00a0", " ").replace("\u202f", " ").strip()


def _nombre(valeur: float):
    valeur = round(valeur, 2)
    return int(valeur) if valeur == int(valeur) else valeur


def _positif(valeur: float, statut: str, motif: str) -> Resultat:
    if valeur <= 0:
        return Resultat(None, INVALIDE, f"valeur <= 0 ({valeur})")
    return Resultat(_nombre(valeur), statut, motif)


# ---------- prix ----------

def normaliser_prix(brut) -> Resultat:
    if est_vide(brut):
        return Resultat(None, MANQUANT, "valeur absente")
    texte = _nettoyer(brut).lower()
    sans_unite = re.sub(rf"\s*{UNITES}\s*$", "", texte).strip()
    unite_retiree = sans_unite != texte

    if unite_retiree and est_vide(sans_unite):
        return Resultat(None, MANQUANT, "marqueur vide suivi d'une unité")

    motif_unite = "suffixe FCFA retiré" if unite_retiree else ""

    m = re.fullmatch(r"(\d+(?:[.,]\d+)?)\s*millions?", sans_unite)
    if m:
        valeur = float(m.group(1).replace(",", ".")) * 1_000_000
        return _positif(valeur, CORRIGE, "unité « millions » explicite")

    if re.fullmatch(r"\d{1,3}(?: \d{3})+(?:[.,]\d+)?", sans_unite):
        valeur = float(sans_unite.replace(" ", "").replace(",", "."))
        return _positif(valeur, CORRIGE, "espaces comme séparateurs de milliers")

    if re.fullmatch(r"\d{1,3}(?:,\d{3})+", sans_unite):
        valeur = float(sans_unite.replace(",", ""))
        return _positif(valeur, CORRIGE, "virgules comme séparateurs de milliers")

    if re.fullmatch(r"-?\d+(?:\.\d+)?", sans_unite):
        statut = CORRIGE if unite_retiree else OK
        return _positif(float(sans_unite), statut, motif_unite)

    return Resultat(None, INVALIDE, f"non numérique : {brut!r}")


# ---------- surface ----------

def normaliser_surface(brut) -> Resultat:
    if est_vide(brut):
        return Resultat(None, MANQUANT, "valeur absente")
    texte = _nettoyer(brut).lower()

    if texte in NOMBRES_EN_LETTRES:
        return _positif(NOMBRES_EN_LETTRES[texte], CORRIGE,
                        "nombre écrit en lettres (dictionnaire)")

    if re.fullmatch(r"-?\d+(?:\.\d+)?", texte):
        return _positif(float(texte), OK, "")

    # « 1,250 » : milliers ou décimale ? On ne devine pas.
    if re.fullmatch(r"-?\d{1,3},\d{3}", texte):
        return Resultat(None, AMBIGU,
                        f"{brut!r} : séparateur de milliers ou virgule décimale ?")

    if re.fullmatch(r"-?\d+,\d+", texte):
        return _positif(float(texte.replace(",", ".")), CORRIGE,
                        "virgule décimale")

    return Resultat(None, INVALIDE, f"non numérique : {brut!r}")


# ---------- dates ----------

def _construire_date(annee: int, mois: int, jour: int,
                     statut: str, motif: str) -> Resultat:
    try:
        return Resultat(date(annee, mois, jour), statut, motif)
    except ValueError:
        return Resultat(None, INVALIDE,
                        f"date impossible ({jour:02d}/{mois:02d}/{annee})")


def normaliser_date(brut, jour_en_premier: Optional[bool] = True) -> Resultat:
    """jour_en_premier=True : convention JJ/MM prouvée pour la source.
    None : convention inconnue, on ne convertit que si la date est sans ambiguïté."""
    if est_vide(brut):
        return Resultat(None, MANQUANT, "valeur absente")
    texte = _nettoyer(brut)

    m = re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})", texte)
    if m:
        a, mo, j = map(int, m.groups())
        return _construire_date(a, mo, j, OK, "")

    m = re.fullmatch(r"(\d{1,2})/(\d{1,2})/(\d{4})", texte)
    if m:
        x, y, annee = map(int, m.groups())
        if jour_en_premier:
            return _construire_date(annee, y, x, CORRIGE,
                                    "JJ/MM/AAAA (convention de la source)")
        if x > 12 >= y:
            return _construire_date(annee, y, x, CORRIGE, "jour déduit (> 12)")
        if y > 12 >= x:
            return _construire_date(annee, x, y, CORRIGE, "jour déduit (> 12)")
        if x == y:
            return _construire_date(annee, x, y, CORRIGE, "jour et mois identiques")
        if x <= 12 and y <= 12:
            return Resultat(None, AMBIGU, f"{texte} : JJ/MM ou MM/JJ ?")
        return Resultat(None, INVALIDE, f"date impossible ({texte})")

    m = re.fullmatch(r"(\d{1,2})\s+([a-zéûè]+)\s+(\d{4})", texte.lower())
    if m and sans_accents(m.group(2)) in MOIS_FR:
        return _construire_date(int(m.group(3)), MOIS_FR[sans_accents(m.group(2))],
                                int(m.group(1)), CORRIGE, "mois en lettres")

    return Resultat(None, INVALIDE, f"format de date non interprétable : {brut!r}")


# ---------- catégories et lieux ----------

def _cle(texte: str) -> str:
    texte = sans_accents(str(texte).lower())
    texte = re.sub(r"[-'’_]", " ", texte)
    return re.sub(r"\s+", " ", texte).strip()


@lru_cache(maxsize=1)
def _table_types_bien() -> dict:
    table = {}
    for canonique, synonymes in CONFIG["types_bien"].items():
        table[_cle(canonique)] = canonique
        for s in synonymes:
            table[_cle(s)] = canonique
    return table


def normaliser_type_bien(brut) -> Resultat:
    if est_vide(brut):
        return Resultat(None, MANQUANT, "valeur absente")
    canonique = _table_types_bien().get(_cle(brut))
    if canonique is None:
        return Resultat(_nettoyer(brut), HORS_REFERENTIEL,
                        f"type absent du référentiel : {brut!r}")
    if _nettoyer(brut) == canonique:
        return Resultat(canonique, OK, "")
    return Resultat(canonique, CORRIGE, "casse ou synonyme ramené au référentiel")


@lru_cache(maxsize=1)
def _tables_geo() -> tuple:
    ref = pd.read_csv(CHEMIN_REFERENTIEL_GEO, dtype=str)
    regions = {_cle(r): r for r in ref["region"].unique()}
    villes = {_cle(v): v for v in ref["ville"].unique()}
    return regions, villes


def _normaliser_lieu(brut, table: dict, libelle: str) -> Resultat:
    if est_vide(brut):
        return Resultat(None, MANQUANT, "valeur absente")
    canonique = table.get(_cle(brut))
    if canonique is None:
        return Resultat(_nettoyer(brut), HORS_REFERENTIEL,
                        f"{libelle} absente du référentiel : {brut!r}")
    if _nettoyer(brut) == canonique:
        return Resultat(canonique, OK, "")
    return Resultat(canonique, CORRIGE, "casse, accents ou tirets ramenés au référentiel")


def normaliser_region(brut) -> Resultat:
    return _normaliser_lieu(brut, _tables_geo()[0], "région")


def normaliser_ville(brut) -> Resultat:
    return _normaliser_lieu(brut, _tables_geo()[1], "ville")
