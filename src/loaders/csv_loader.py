import pandas as pd

SOURCES_DIR = "data/raw/immoanalyse_dataset/sources"


def charger_plateforme() -> pd.DataFrame:
    df = pd.read_csv(f"{SOURCES_DIR}/plateforme_immo_sn.csv", sep=";", dtype=str)
    df["source"] = "plateforme"
    return df


def charger_historique() -> pd.DataFrame:
    df = pd.read_csv(
        f"{SOURCES_DIR}/import_historique.csv", sep=";", encoding="latin-1", dtype=str
    )
    df["source"] = "historique"
    return df


def charger_notaires() -> pd.DataFrame:
    df = pd.read_csv(f"{SOURCES_DIR}/notaires.csv", sep=",", dtype=str)
    df["source"] = "notaires"
    return df