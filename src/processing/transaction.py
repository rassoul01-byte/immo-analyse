"""Type de transaction (vente ou location) pour les sources qui ne le fournissent pas.

Voir D-004 et D-011. Preuves, dans cet ordre :
1. la valeur fournie par la source, si elle existe ;
2. la nature de la source (actes notariés, ventes historiques) ;
3. le statut (« Loué », « Vendu », « En vente »), contrôlé par l'échelle de prix ;
4. l'échelle de prix seule.
En cas de contradiction ou d'absence de preuve : ambigu, on ne devine pas.
"""
from src.config import CONFIG
from src.processing.normalisation import (
    AMBIGU, CORRIGE, INVALIDE, OK, Resultat, est_vide, sans_accents,
)

VENTE = "vente"
LOCATION = "location"

SEUIL = CONFIG["seuils"]["seuil_location_vente_fcfa"]
SOURCES_DE_VENTES = {"notaires", "historique"}
STATUTS_LOCATION = {"loue"}
STATUTS_VENTE = {"vendu", "en vente", "vente conclue", "acte signe"}


def _cle_statut(statut) -> str:
    return "" if est_vide(statut) else sans_accents(str(statut).strip().lower())


def deduire_type_transaction(source, type_brut, statut, prix) -> Resultat:
    """prix : valeur déjà normalisée (nombre) ou None."""
    # 1. valeur fournie par la source
    if not est_vide(type_brut):
        valeur = str(type_brut).strip().lower()
        if valeur in (VENTE, LOCATION):
            return Resultat(valeur, OK, "")
        return Resultat(None, INVALIDE, f"type de transaction inconnu : {type_brut!r}")

    prix_de_loyer = prix is not None and prix < SEUIL

    # 2. nature de la source
    if source in SOURCES_DE_VENTES:
        if prix_de_loyer:
            return Resultat(None, AMBIGU,
                            "source de ventes mais prix de l'échelle des loyers")
        return Resultat(VENTE, CORRIGE, "source de ventes (acte notarié / date de vente)")

    # 3. statut, contrôlé par l'échelle de prix
    cle = _cle_statut(statut)
    if cle in STATUTS_LOCATION:
        if prix is not None and not prix_de_loyer:
            return Resultat(None, AMBIGU, "statut « loué » mais prix de l'échelle des ventes")
        return Resultat(LOCATION, CORRIGE, "statut « loué »")
    if cle in STATUTS_VENTE:
        if prix_de_loyer:
            return Resultat(None, AMBIGU, f"statut « {statut} » mais prix de l'échelle des loyers")
        return Resultat(VENTE, CORRIGE, f"statut « {statut} »")

    # 4. échelle de prix seule (statut absent ou neutre comme « Disponible »)
    if prix is None:
        return Resultat(None, AMBIGU, "ni statut décisif ni prix")
    if prix_de_loyer:
        return Resultat(LOCATION, CORRIGE, f"échelle de prix (< {SEUIL:,} FCFA)".replace(",", " "))
    return Resultat(VENTE, CORRIGE, f"échelle de prix (>= {SEUIL:,} FCFA)".replace(",", " "))
