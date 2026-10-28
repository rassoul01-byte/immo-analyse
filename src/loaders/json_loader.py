import json
import pandas as pd

SOURCES_DIR = "data/raw/immoanalyse_dataset/sources"


def charger_particuliers() -> pd.DataFrame:
    with open(f"{SOURCES_DIR}/particuliers.json", encoding="utf-8") as f:
        brut = json.load(f)

    df = pd.json_normalize(brut)
    # 1. Renommer les colonnes "annonce.details.prix" -> "prix", etc.
    # 2. Ajouter la colonne "source"
    return df