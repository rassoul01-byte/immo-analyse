import json
import pandas as pd

SOURCES_DIR = "data/raw/immoanalyse_dataset/sources"

RENOMMAGE = {
    "annonce.id": "id_local",
    "annonce.date": "date",
    "annonce.localisation.region": "region",
    "annonce.localisation.ville": "ville",
    "annonce.details.type": "type_bien",
    "annonce.details.transaction": "type_transaction",
    "annonce.details.prix": "prix",
    "annonce.details.surface": "surface",
    "annonce.details.chambres": "chambres",
    "annonce.details.sdb": "salles_bain",
    "annonce.statut": "statut",
}


def charger_particuliers() -> pd.DataFrame:
    with open(f"{SOURCES_DIR}/particuliers.json", encoding="utf-8") as f:
        brut = json.load(f)

    df = pd.json_normalize(brut).rename(columns=RENOMMAGE)
    df = df.astype("string")
    df["source"] = "particuliers"
    return df