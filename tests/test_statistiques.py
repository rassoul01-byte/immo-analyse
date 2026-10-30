import numpy as np
import pandas as pd

from src.analysis.statistiques import (
    MIN_EFFECTIF, loyers_mensuels, resume_ventes_par, statistiques, ventes,
)


def test_statistiques_valeurs_connues():
    s = statistiques([1, 2, 3, 4, 100])
    assert s["n"] == 5 and s["moyenne"] == 22 and s["mediane"] == 3
    assert (s["min"], s["max"]) == (1, 100)


def test_la_mediane_resiste_aux_valeurs_extremes_pas_la_moyenne():
    s = statistiques([10, 11, 12, 13, 10_000])
    assert s["mediane"] == 12 and s["moyenne"] > 2000


def test_statistiques_ignorent_les_valeurs_manquantes():
    assert statistiques([1.0, np.nan, 3.0])["n"] == 2


def test_statistiques_sur_serie_vide():
    s = statistiques([])
    assert s["n"] == 0 and np.isnan(s["mediane"])


def test_ecart_type_indefini_pour_une_seule_valeur():
    assert np.isnan(statistiques([5])["ecart_type"])


def jeu():
    return pd.DataFrame({
        "type_transaction": ["vente", "vente", "vente", "location", "location"],
        "type_bien": ["Villa", "Villa", "Terrain", "Studio", "Studio"],
        "prix": [100.0, 300.0, 50.0, 200_000.0, 400_000.0],
        "surface": [10.0, 20.0, 0.0, 30.0, 40.0],
        "periodicite": [None, None, None, "mensuel", None],
    })


def test_prix_m2_exclut_locations_et_surfaces_nulles():
    v = ventes(jeu())
    assert len(v) == 2                                   # la surface 0 et les locations sont exclues
    assert sorted(v["prix_m2"]) == [10.0, 15.0]


def test_loyers_exigent_une_periodicite_mensuelle():
    assert len(loyers_mensuels(jeu())) == 1              # la périodicité inconnue n'est pas devinée


def test_effectif_faible_signale():
    v = ventes(jeu())
    r = resume_ventes_par(v, "type_bien")
    assert MIN_EFFECTIF > 2 and not r["effectif_fiable"].any()