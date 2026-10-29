import pandas as pd

from src.loaders.csv_loader import (
    charger_historique,
    charger_notaires,
    charger_plateforme,
)
from src.loaders.excel_loader import charger_teranga
from src.loaders.json_loader import charger_particuliers

# Schéma commun : colonnes présentes dans toutes les sources (NA si absentes)
COLONNES_COMMUNES = [
    "source", "id_local", "date", "type_transaction", "type_bien",
    "region", "ville", "prix", "surface", "chambres", "salles_bain", "statut",
]

# Colonnes propres à certaines sources, conservées pour ne rien perdre
COLONNES_ADDITIONNELLES = [
    "quartier", "devise", "description", "date_expiration", "commercial", "pieces",
]

COLONNES_FINALES = COLONNES_COMMUNES + COLONNES_ADDITIONNELLES

MAPPING_PLATEFORME = {
    "ref_plateforme": "id_local",
    "date_mise_en_ligne": "date",
    "categorie": "type_bien",
    "commune": "ville",
    # region, type_transaction, prix, surface, devise, quartier,
    # description, statut, date_expiration : déjà au bon nom
    # sdb et pieces : voir ci-dessous
    "sdb": "salles_bain",
}

MAPPING_TERANGA = {
    "Code": "id_local",
    "Date": "date",
    "Region": "region",
    "Ville": "ville",
    "Type": "type_bien",
    "Prix_FCFA": "prix",
    "Surface_m2": "surface",
    "Chambres": "chambres",
    "SDB": "salles_bain",
    "Statut": "statut",
    "Commercial": "commercial",
}

MAPPING_NOTAIRES = {
    "id_acte": "id_local",
    "date_acte": "date",
    "montant_fcfa": "prix",
    "superficie": "surface",
    "nb_chambres": "chambres",
    # region, ville, type_bien, statut : déjà au bon nom
}

MAPPING_HISTORIQUE = {
    "ID": "id_local",
    "DateVente": "date",
    "Region": "region",
    "Ville": "ville",
    "TypeBien": "type_bien",
    "Prix": "prix",
    "Surface": "surface",
    "Chambres": "chambres",
    "SallesBain": "salles_bain",
}

# Les particuliers sont déjà renommés dans json_loader.py
MAPPING_PARTICULIERS = {}


def harmoniser(df: pd.DataFrame, mapping: dict) -> pd.DataFrame:
    """Renomme les colonnes d'une source vers le schéma commun.

    Une colonne absente de la source est remplie avec pd.NA : c'est une
    valeur non évaluable, pas une valeur fausse.
    """
    df = df.rename(columns=mapping)
    for col in COLONNES_FINALES:
        if col not in df.columns:
            df[col] = pd.NA
    return df[COLONNES_FINALES]


def charger_toutes_les_sources() -> pd.DataFrame:
    """Charge les 5 sources, les harmonise et les assemble en un seul DataFrame."""
    sources = [
        (charger_plateforme(), MAPPING_PLATEFORME),
        (charger_teranga(), MAPPING_TERANGA),
        (charger_particuliers(), MAPPING_PARTICULIERS),
        (charger_notaires(), MAPPING_NOTAIRES),
        (charger_historique(), MAPPING_HISTORIQUE),
    ]
    morceaux = [harmoniser(df, mapping) for df, mapping in sources]
    return pd.concat(morceaux, ignore_index=True)