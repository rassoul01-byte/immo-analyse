"""Règles métier d'ImmoAnalyse. Les seuils viennent de config/regles.json."""
from datetime import date

import pandas as pd

from src.config import CHEMIN_REFERENTIEL_GEO, CONFIG
from src.processing.normalisation import CORRIGE, OK
from src.validation.regle import (
    AVERTISSEMENT, BLOQUANTE, Regle, conforme, non_conforme, non_evaluable,
)

SEUILS = CONFIG["seuils"]
VALIDES = (OK, CORRIGE)

# D-012 : le cahier des charges (6.1, « tableau de remplacement ») prévaut sur
# regles_metier.md : un type hors référentiel est mis en quarantaine.
GRAVITE_TYPE_HORS_REFERENTIEL = BLOQUANTE


def _present(valeur) -> bool:
    return not pd.isna(valeur)


def _valide(ligne, champ) -> bool:
    return ligne.get(f"{champ}_statut") in VALIDES


def _regions_par_ville() -> dict:
    ref = pd.read_csv(CHEMIN_REFERENTIEL_GEO, dtype=str)
    return ref.groupby("ville")["region"].apply(set).to_dict()


REGIONS_PAR_VILLE = _regions_par_ville()


# ---------- contrôles bloquants ----------

def _identifiant(l):
    return conforme() if _present(l["id_local"]) else non_conforme("identifiant absent")


def _type_transaction(l):
    if _present(l["type_transaction"]):
        return conforme()
    return non_conforme("type de transaction non interprétable")


def _prix(l):
    if _valide(l, "prix"):
        return conforme()
    return non_conforme(f"prix {l['prix_statut']}")


def _surface(l):
    if _valide(l, "surface"):
        return conforme()
    return non_conforme(f"surface {l['surface_statut']}")


def _date_interpretable(l):
    if _valide(l, "date"):
        return conforme()
    return non_conforme(f"date {l['date_statut']}")


def _type_bien(l):
    if _valide(l, "type_bien"):
        return conforme()
    return non_conforme(f"type de bien {l['type_bien_statut']}")


def fabriquer_regle_date_future(date_execution: date) -> Regle:
    def controle(l):
        if not _valide(l, "date"):
            return non_evaluable("date non interprétable")
        if l["date"] > date_execution:
            return non_conforme(f"date future ({l['date']})")
        return conforme()
    return Regle("B06", "Date non future (par rapport à l'exécution)", BLOQUANTE, controle)


# ---------- contrôles d'avertissement ----------

def _surface_atypique(l):
    if not _valide(l, "surface"):
        return non_evaluable("surface non exploitable")
    s = SEUILS["surface_m2"]
    if l["surface"] < s["min_atypique"] or l["surface"] > s["max_atypique"]:
        return non_conforme(f"surface atypique ({l['surface']} m²)")
    return conforme()


def _prix_atypique(l):
    if l["type_transaction"] != "vente" or not _valide(l, "prix"):
        return non_evaluable("pas une vente avec prix exploitable")
    s = SEUILS["prix_fcfa"]
    if l["prix"] < s["min_atypique"] or l["prix"] > s["max_atypique"]:
        return non_conforme(f"prix atypique ({l['prix']:.0f} FCFA)")
    return conforme()


def _loyer_atypique(l):
    if l["type_transaction"] != "location" or not _valide(l, "prix"):
        return non_evaluable("pas une location avec prix exploitable")
    if l["periodicite"] != "mensuel":
        return non_evaluable("périodicité non mensuelle ou inconnue")
    s = SEUILS["loyer_mensuel_fcfa"]
    if l["prix"] < s["min_atypique"] or l["prix"] > s["max_atypique"]:
        return non_conforme(f"loyer mensuel atypique ({l['prix']:.0f} FCFA)")
    return conforme()


def _prix_m2(l):
    fourchettes = CONFIG["fourchettes_indicatives"]
    if (l["type_transaction"] != "vente" or not _valide(l, "prix")
            or not _valide(l, "surface") or l["type_bien"] not in fourchettes):
        return non_evaluable("vente avec prix, surface et type connus requis")
    f = fourchettes[l["type_bien"]]
    bas = f["prix_min"] / f["surface_max"]
    haut = f["prix_max"] / f["surface_min"]
    m2 = l["prix"] / l["surface"]
    if m2 < bas or m2 > haut:
        return non_conforme(f"prix au m² hors fourchette ({m2:,.0f} FCFA/m²)".replace(",", " "))
    return conforme()


def _chambres_atypiques(l):
    if not _present(l["chambres"]):
        return non_evaluable("chambres non renseigné")
    if l["type_bien"] in ("Appartement", "Studio") and l["chambres"] > SEUILS["chambres_max_appartement_studio"]:
        return non_conforme(f"{int(l['chambres'])} chambres pour un {l['type_bien']}")
    return conforme()


def _salles_bain(l):
    if not (_present(l["chambres"]) and _present(l["salles_bain"])):
        return non_evaluable("chambres ou salles de bain non renseigné")
    if l["salles_bain"] > l["chambres"] + SEUILS["salles_bain_marge_sur_chambres"]:
        return non_conforme(f"{int(l['salles_bain'])} salles de bain pour {int(l['chambres'])} chambres")
    return conforme()


def _region_ville(l):
    if not (_valide(l, "ville") and _valide(l, "region")):
        return non_evaluable("ville ou région absente du référentiel")
    regions = REGIONS_PAR_VILLE.get(l["ville"])
    if regions is None:
        return non_evaluable("ville inconnue du référentiel")
    if l["region"] in regions:
        return conforme()
    return non_conforme(f"{l['ville']} n'est pas dans {l['region']}")


def _periodicite_location(l):
    if l["type_transaction"] != "location":
        return non_evaluable("pas une location")
    if _present(l["periodicite"]):
        return conforme()
    return non_conforme("périodicité du loyer non fournie")


def construire_regles(date_execution: date) -> list:
    return [
        Regle("B01", "Identifiant local présent", BLOQUANTE, _identifiant),
        Regle("B02", "Type de transaction interprétable", BLOQUANTE, _type_transaction),
        Regle("B03", "Prix numérique strictement positif", BLOQUANTE, _prix),
        Regle("B04", "Surface numérique strictement positive", BLOQUANTE, _surface),
        Regle("B05", "Date interprétable", BLOQUANTE, _date_interpretable),
        fabriquer_regle_date_future(date_execution),
        Regle("B07", "Type de bien dans le référentiel", GRAVITE_TYPE_HORS_REFERENTIEL, _type_bien),
        Regle("A01", "Surface non atypique", AVERTISSEMENT, _surface_atypique),
        Regle("A02", "Prix de vente non atypique", AVERTISSEMENT, _prix_atypique),
        Regle("A03", "Loyer mensuel non atypique", AVERTISSEMENT, _loyer_atypique),
        Regle("A04", "Prix au m² dans la fourchette du type", AVERTISSEMENT, _prix_m2),
        Regle("A05", "Nombre de chambres plausible", AVERTISSEMENT, _chambres_atypiques),
        Regle("A06", "Salles de bain <= chambres + 2", AVERTISSEMENT, _salles_bain),
        Regle("A07", "Ville cohérente avec la région", AVERTISSEMENT, _region_ville),
        Regle("A08", "Périodicité du loyer renseignée", AVERTISSEMENT, _periodicite_location),
    ]
