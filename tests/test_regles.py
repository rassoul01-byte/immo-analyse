from datetime import date

import pandas as pd
import pytest

from src.validation.moteur import appliquer_regles, classer
from src.validation.regle import CONFORME, NON_CONFORME, NON_EVALUABLE
from src.validation.regles_metier import construire_regles

AUJOURDHUI = date(2026, 10, 29)
REGLES = {r.code: r for r in construire_regles(AUJOURDHUI)}


def ligne(**surcharges):
    """Enregistrement conforme par défaut ; on surcharge ce qu'on teste."""
    base = {
        "id_ligne": 0, "source": "plateforme", "id_local": "PLT-1",
        "date": date(2024, 3, 1), "date_statut": "ok",
        "type_transaction": "vente", "type_bien": "Appartement", "type_bien_statut": "ok",
        "region": "Dakar", "region_statut": "ok", "ville": "Dakar", "ville_statut": "ok",
        "prix": 60_000_000.0, "prix_statut": "ok",
        "surface": 100.0, "surface_statut": "ok",
        "chambres": 3, "salles_bain": 2, "periodicite": None,
    }
    base.update(surcharges)
    return base


def etat(code, **surcharges):
    return REGLES[code].evaluer(ligne(**surcharges)).etat


def test_ligne_de_reference_conforme_a_toutes_les_regles():
    for code, regle in REGLES.items():
        assert regle.evaluer(ligne()).etat in (CONFORME, NON_EVALUABLE), code


# ---------- bloquantes ----------
def test_b01_identifiant():
    assert etat("B01", id_local=None) == NON_CONFORME
    assert etat("B01") == CONFORME


def test_b02_type_transaction():
    assert etat("B02", type_transaction=None) == NON_CONFORME


@pytest.mark.parametrize("statut", ["manquant", "invalide"])
def test_b03_prix(statut):
    assert etat("B03", prix=None, prix_statut=statut) == NON_CONFORME


def test_b04_surface():
    assert etat("B04", surface=None, surface_statut="invalide") == NON_CONFORME


def test_b05_date():
    assert etat("B05", date=None, date_statut="invalide") == NON_CONFORME


def test_b06_date_future():
    assert etat("B06", date=date(2028, 12, 1)) == NON_CONFORME


def test_b06_cas_limite_date_du_jour_acceptee():
    assert etat("B06", date=AUJOURDHUI) == CONFORME


def test_b06_non_evaluable_si_date_invalide():
    assert etat("B06", date=None, date_statut="invalide") == NON_EVALUABLE


def test_b07_type_hors_referentiel():
    assert etat("B07", type_bien_statut="hors_referentiel") == NON_CONFORME


# ---------- avertissements ----------
@pytest.mark.parametrize("surface, attendu", [
    (4.9, NON_CONFORME), (5.0, CONFORME), (2000.0, CONFORME), (2000.1, NON_CONFORME),
])
def test_a01_bornes_de_surface(surface, attendu):
    assert etat("A01", surface=surface) == attendu


def test_a02_prix_atypique_vente():
    assert etat("A02", prix=50_000.0) == NON_CONFORME
    assert etat("A02", prix=3_000_000_000.0) == NON_CONFORME


def test_a02_non_evaluable_pour_une_location():
    assert etat("A02", type_transaction="location") == NON_EVALUABLE


def test_a03_loyer_mensuel():
    loc = dict(type_transaction="location", periodicite="mensuel")
    assert etat("A03", prix=10_000.0, **loc) == NON_CONFORME
    assert etat("A03", prix=250_000.0, **loc) == CONFORME


def test_a03_non_evaluable_sans_periodicite():
    # on ne devine pas la périodicité
    assert etat("A03", type_transaction="location", prix=10_000.0) == NON_EVALUABLE


def test_a04_prix_au_m2():
    # Appartement : 25 M / 180 m² minimum, 120 M / 45 m² maximum
    assert etat("A04", prix=60_000_000.0, surface=100.0) == CONFORME
    assert etat("A04", prix=60_000_000.0, surface=1000.0) == NON_CONFORME


def test_a04_non_evaluable_pour_une_location():
    assert etat("A04", type_transaction="location") == NON_EVALUABLE


def test_a05_trop_de_chambres():
    assert etat("A05", type_bien="Studio", chambres=11) == NON_CONFORME
    assert etat("A05", type_bien="Studio", chambres=10) == CONFORME
    assert etat("A05", type_bien="Villa", chambres=11) == CONFORME  # règle limitée aux appartements et studios


def test_a05_non_evaluable_sans_chambres():
    assert etat("A05", chambres=float("nan")) == NON_EVALUABLE


def test_a06_salles_de_bain():
    assert etat("A06", chambres=1, salles_bain=4) == NON_CONFORME
    assert etat("A06", chambres=1, salles_bain=3) == CONFORME       # cas limite : chambres + 2


def test_a07_region_ville():
    assert etat("A07", ville="Dakar", region="Ziguinchor") == NON_CONFORME
    assert etat("A07", ville="Pikine", region="Dakar") == CONFORME


def test_a08_periodicite_des_locations():
    assert etat("A08", type_transaction="location", periodicite=None) == NON_CONFORME
    assert etat("A08", type_transaction="location", periodicite="mensuel") == CONFORME
    assert etat("A08") == NON_EVALUABLE   # une vente n'a pas de périodicité


# ---------- moteur ----------
def test_taux_de_conformite_utilise_les_evaluables_seulement():
    df = pd.DataFrame([
        ligne(id_ligne=0),
        ligne(id_ligne=1, surface=1.0),
        ligne(id_ligne=2, surface=None, surface_statut="manquant"),   # non évaluable pour A01
    ])
    violations, rapport = appliquer_regles(df, list(REGLES.values()))
    a01 = rapport[rapport.code == "A01"].iloc[0]
    assert (a01.evaluables, a01.conformes, a01.non_conformes, a01.non_evaluables) == (2, 1, 1, 1)
    assert a01.taux_conformite == 50.0


def test_un_enregistrement_est_compte_une_seule_fois():
    df = pd.DataFrame([ligne(id_ligne=0, id_local=None, surface=1.0)])  # bloquante + avertissement
    violations, _ = appliquer_regles(df, list(REGLES.values()))
    classe = classer(df, violations)
    assert classe["classement"].tolist() == ["quarantaine"]
