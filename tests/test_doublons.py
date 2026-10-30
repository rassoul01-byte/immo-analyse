from datetime import date

import pandas as pd

from src.validation.doublons import (
    CONFLIT_ID, CONFLIT_PRIX, DOUBLON_ECARTE, EXACT, PROBABLE,
    detecter_doublons, integrer_au_classement,
)


def bien(id_ligne, **surcharges):
    base = {
        "id_ligne": id_ligne, "source": "plateforme", "id_local": f"PLT-{id_ligne}",
        "type_transaction": "vente", "type_bien": "Villa", "region": "Dakar", "ville": "Dakar",
        "prix": 100_000_000.0, "surface": 200.0, "chambres": 4, "salles_bain": 3,
        "date": date(2024, 5, 10),
    }
    base.update(surcharges)
    return base


def liens(*biens):
    return detecter_doublons(pd.DataFrame(list(biens)))


def types(l):
    return sorted(l["type_lien"].tolist())


def test_doublon_exact_meme_source_meme_id():
    l = liens(bien(0, id_local="X"), bien(1, id_local="X"))
    assert types(l) == [EXACT]


def test_conflit_identifiant_meme_id_valeurs_differentes():
    l = liens(bien(0, id_local="X"), bien(1, id_local="X", prix=90_000_000.0))
    assert types(l) == [CONFLIT_ID]
    assert "prix" in l.iloc[0]["motif"]


def test_doublon_probable_entre_sources():
    a = bien(0, source="teranga", id_local="AGT-1")
    b = bien(1, source="particuliers", id_local="PRT-9", prix=103_000_000.0,
             surface=200.2, date=date(2024, 5, 25))
    assert types(liens(a, b)) == [PROBABLE]


def test_conflit_de_prix_meme_bien_prix_contradictoires():
    a = bien(0, source="teranga")
    b = bien(1, source="notaires", prix=150_000_000.0)
    assert types(liens(a, b)) == [CONFLIT_PRIX]


def test_biens_trop_eloignes_dans_le_temps_ne_sont_pas_lies():
    a = bien(0, source="teranga")
    b = bien(1, source="notaires", date=date(2021, 1, 1))
    assert liens(a, b).empty


def test_villes_differentes_ne_sont_pas_liees():
    assert liens(bien(0), bien(1, source="teranga", ville="Thiès")).empty


def test_bornes_de_tolerance_date():
    # 30 jours exactement : lié ; 31 jours : non lié
    a = bien(0, source="teranga")
    assert types(liens(a, bien(1, source="notaires", date=date(2024, 6, 9)))) == [PROBABLE]
    assert liens(a, bien(1, source="notaires", date=date(2024, 6, 10))).empty


def test_bornes_de_tolerance_surface():
    # 0,2 % de 200 m² = 0,4 m² ; au-delà, ce n'est plus le même bien
    a = bien(0, source="teranga")
    assert types(liens(a, bien(1, source="notaires", surface=200.4))) == [PROBABLE]
    assert liens(a, bien(1, source="notaires", surface=201.0)).empty


def test_chambres_connues_et_differentes_biens_distincts():
    a = bien(0, source="teranga", chambres=2)
    assert liens(a, bien(1, source="notaires", chambres=5)).empty


def test_chambres_inconnues_ne_bloquent_pas_le_rapprochement():
    a = bien(0, source="plateforme", chambres=float("nan"))
    assert types(liens(a, bien(1, source="notaires", chambres=5))) == [PROBABLE]


def test_sans_prix_pas_de_signalement():
    a = bien(0, source="teranga", prix=float("nan"))
    assert liens(a, bien(1, source="notaires")).empty


def test_trois_copies_identiques_deux_sont_ecartees():
    l = liens(bien(0, id_local="X"), bien(1, id_local="X"), bien(2, id_local="X"))
    classe = pd.DataFrame({"id_ligne": [0, 1, 2], "classement": ["entierement_conforme"] * 3})
    sortie = integrer_au_classement(classe, l)
    assert sortie["classement"].tolist() == ["entierement_conforme", DOUBLON_ECARTE, DOUBLON_ECARTE]


def test_doublon_probable_conserve_avec_avertissement_sans_fusion():
    l = liens(bien(0, source="teranga"), bien(1, source="notaires", prix=102_000_000.0))
    classe = pd.DataFrame({"id_ligne": [0, 1], "classement": ["entierement_conforme", "quarantaine"]})
    sortie = integrer_au_classement(classe, l)
    # le conforme passe en avertissement ; la quarantaine reste en quarantaine ; aucune ligne supprimée
    assert sortie["classement"].tolist() == ["conserve_avec_avertissement", "quarantaine"]
