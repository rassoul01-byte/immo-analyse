import pandas as pd

SOURCES_DIR = "data/raw/immoanalyse_dataset/sources"
FICHIER_TERANGA = f"{SOURCES_DIR}/agence_teranga.xlsx"


def charger_teranga() -> pd.DataFrame:
    df = pd.read_excel(FICHIER_TERANGA, sheet_name="Annonces", dtype=str)
    df["source"] = "teranga"
    return df


def charger_teranga_params() -> dict:
    df = pd.read_excel(FICHIER_TERANGA, sheet_name="Params", dtype=str)
    return dict(zip(df["Parametre"], df["Valeur"]))