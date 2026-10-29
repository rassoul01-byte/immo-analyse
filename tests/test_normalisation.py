from datetime import date

import pandas as pd
import pytest

from src.processing.normalisation import (
    AMBIGU, CORRIGE, HORS_REFERENTIEL, INVALIDE, MANQUANT, OK,
    normaliser_date, normaliser_prix, normaliser_surface,
    normaliser_type_bien, normaliser_ville,
)


# ---------- prix ----------
@pytest.mark.parametrize("brut, valeur, statut", [
    ("18152000", 18152000, OK),
    ("18152000.0", 18152000, OK),
    ("57.62 millions", 57620000, CORRIGE),
    ("438 746 000", 438746000, CORRIGE),
    ("65575000 FCFA", 65575000, CORRIGE),
    ("1,250,000", 1250000, CORRIGE),
    ("\u00a0438\u00a0746\u00a0000", 438746000, CORRIGE),
])
def test_prix_valides(brut, valeur, statut):
    r = normaliser_prix(brut)
    assert (r.valeur, r.statut) == (valeur, statut)


@pytest.mark.parametrize("brut, statut", [
    ("à négocier", INVALIDE),
    ("0", INVALIDE),
    ("-5000", INVALIDE),
    ("None FCFA", MANQUANT),
    ("", MANQUANT),
    (None, MANQUANT),
    (pd.NA, MANQUANT),
])
def test_prix_non_exploitables(brut, statut):
    r = normaliser_prix(brut)
    assert r.statut == statut and r.valeur is None


# ---------- surface ----------
@pytest.mark.parametrize("brut, valeur, statut", [
    ("50.0", 50, OK),
    ("92,4", 92.4, CORRIGE),
    ("1354,0", 1354, CORRIGE),
    ("quatre-vingt", 80, CORRIGE),
])
def test_surface_valides(brut, valeur, statut):
    r = normaliser_surface(brut)
    assert (r.valeur, r.statut) == (valeur, statut)


def test_surface_ambigue_ne_se_devine_pas():
    r = normaliser_surface("1,250")
    assert r.statut == AMBIGU and r.valeur is None


@pytest.mark.parametrize("brut, statut", [
    ("-12", INVALIDE), ("0", INVALIDE), ("grande", INVALIDE), ("", MANQUANT),
])
def test_surface_non_exploitable(brut, statut):
    assert normaliser_surface(brut).statut == statut


# ---------- dates ----------
def test_date_iso():
    assert normaliser_date("2024-03-01").valeur == date(2024, 3, 1)


def test_date_jj_mm_convention_source():
    r = normaliser_date("05/06/2018", jour_en_premier=True)
    assert r.valeur == date(2018, 6, 5) and r.statut == CORRIGE


def test_date_ambigue_sans_convention():
    assert normaliser_date("05/06/2018", jour_en_premier=None).statut == AMBIGU


def test_date_deduite_sans_convention():
    r = normaliser_date("17/06/2019", jour_en_premier=None)
    assert r.valeur == date(2019, 6, 17)


@pytest.mark.parametrize("brut", ["32/13/2024", "30/02/2024", "hier", "2024-13-45"])
def test_date_impossible(brut):
    assert normaliser_date(brut).statut == INVALIDE


def test_date_mois_en_lettres():
    assert normaliser_date("3 février 2024").valeur == date(2024, 2, 3)


# ---------- catégories et lieux ----------
@pytest.mark.parametrize("brut, valeur, statut", [
    ("Appartement", "Appartement", OK),
    ("APPARTEMENT", "Appartement", CORRIGE),
    ("appart", "Appartement", CORRIGE),
    ("LOCAL COMMERCIAL", "Local commercial", CORRIGE),
    ("bureau", "Local commercial", CORRIGE),
])
def test_type_bien(brut, valeur, statut):
    r = normaliser_type_bien(brut)
    assert (r.valeur, r.statut) == (valeur, statut)


def test_type_bien_hors_referentiel():
    assert normaliser_type_bien("château").statut == HORS_REFERENTIEL


@pytest.mark.parametrize("brut, valeur", [
    ("GOSSAS", "Gossas"), ("KÉDOUGOU", "Kédougou"), ("joal-fadiouth", "Joal-Fadiouth"),
    ("KEUR MASSAR", "Keur Massar"), ("ziguinchor", "Ziguinchor"),
    ("Kaolack-Fatick", "Kaolack-Fatick"),
])
def test_ville_normalisee(brut, valeur):
    assert normaliser_ville(brut).valeur == valeur


def test_ville_hors_referentiel_non_corrigee():
    r = normaliser_ville("Atlantis")
    assert r.statut == HORS_REFERENTIEL and r.valeur == "Atlantis"
