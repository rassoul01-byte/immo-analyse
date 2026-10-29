import pytest

from src.processing.normalisation import AMBIGU, CORRIGE, INVALIDE, OK
from src.processing.transaction import (
    LOCATION, SEUIL, VENTE, deduire_type_transaction,
)


def test_valeur_fournie_conservee():
    r = deduire_type_transaction("plateforme", "vente", "Vendu", 50_000_000)
    assert (r.valeur, r.statut) == (VENTE, OK)


def test_valeur_fournie_inconnue():
    assert deduire_type_transaction("plateforme", "échange", None, None).statut == INVALIDE


@pytest.mark.parametrize("source", ["notaires", "historique"])
def test_sources_de_ventes(source):
    r = deduire_type_transaction(source, None, None, 30_000_000)
    assert (r.valeur, r.statut) == (VENTE, CORRIGE)


def test_source_de_ventes_avec_prix_de_loyer_est_ambigue():
    assert deduire_type_transaction("notaires", None, "Vendu", 300_000).statut == AMBIGU


def test_statut_loue():
    r = deduire_type_transaction("teranga", None, "Loué", 250_000)
    assert r.valeur == LOCATION


@pytest.mark.parametrize("statut", ["Vendu", "En vente"])
def test_statut_vente(statut):
    assert deduire_type_transaction("teranga", None, statut, 80_000_000).valeur == VENTE


def test_statut_contredit_par_le_prix():
    assert deduire_type_transaction("teranga", None, "Vendu", 250_000).statut == AMBIGU
    assert deduire_type_transaction("teranga", None, "Loué", 80_000_000).statut == AMBIGU


def test_disponible_tranche_par_le_prix():
    assert deduire_type_transaction("teranga", None, "Disponible", 285_000).valeur == LOCATION
    assert deduire_type_transaction("teranga", None, "Disponible", 40_000_000).valeur == VENTE


def test_cas_limite_au_seuil():
    # le seuil est exclu côté loyer : prix == SEUIL -> vente
    assert deduire_type_transaction("teranga", None, "Disponible", SEUIL).valeur == VENTE
    assert deduire_type_transaction("teranga", None, "Disponible", SEUIL - 1).valeur == LOCATION


def test_aucune_preuve():
    r = deduire_type_transaction("teranga", None, "Disponible", None)
    assert r.statut == AMBIGU and r.valeur is None
