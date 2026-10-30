"""Analyses numériques sur les données propres (Étape 5).

Règle de base : ventes et locations ne se mélangent jamais. Un loyer de
250 000 FCFA n'est pas comparable à un prix de vente de 250 000 FCFA.
Les prix de vente sont des prix demandés (annonces), pas des prix de
transaction conclue.
"""
from pathlib import Path

import numpy as np
import pandas as pd

MIN_EFFECTIF = 5  # en dessous, une médiane de groupe n'est pas fiable


def charger_propres(chemin: Path) -> pd.DataFrame:
    return pd.read_csv(chemin, dtype={"id_local": str})


def ventes(df: pd.DataFrame) -> pd.DataFrame:
    """Ventes exploitables, avec le prix au m² (prix / surface)."""
    v = df[(df["type_transaction"] == "vente") & (df["prix"] > 0) & (df["surface"] > 0)].copy()
    v["prix_m2"] = np.divide(v["prix"].to_numpy(dtype=float), v["surface"].to_numpy(dtype=float))
    return v


def loyers_mensuels(df: pd.DataFrame) -> pd.DataFrame:
    """Seuls les loyers dont la périodicité est connue comme mensuelle sont comparables."""
    return df[(df["type_transaction"] == "location") & (df["periodicite"] == "mensuel")
              & (df["prix"] > 0)].copy()


def statistiques(valeurs) -> dict:
    x = np.asarray(valeurs, dtype=float)
    x = x[~np.isnan(x)]
    if x.size == 0:
        return {"n": 0, "moyenne": np.nan, "mediane": np.nan, "ecart_type": np.nan,
                "min": np.nan, "q1": np.nan, "q3": np.nan, "max": np.nan}
    return {
        "n": int(x.size),
        "moyenne": float(np.mean(x)),
        "mediane": float(np.median(x)),
        "ecart_type": float(np.std(x, ddof=1)) if x.size > 1 else np.nan,
        "min": float(np.min(x)),
        "q1": float(np.percentile(x, 25)),
        "q3": float(np.percentile(x, 75)),
        "max": float(np.max(x)),
    }


def resume_ventes_par(df_ventes: pd.DataFrame, colonne: str) -> pd.DataFrame:
    lignes = []
    for cle, groupe in df_ventes.groupby(colonne):
        lignes.append({
            colonne: cle,
            "n": len(groupe),
            "prix_median": float(np.median(groupe["prix"])),
            "prix_moyen": float(np.mean(groupe["prix"])),
            "prix_m2_median": float(np.median(groupe["prix_m2"])),
            "surface_mediane": float(np.median(groupe["surface"])),
            "effectif_fiable": len(groupe) >= MIN_EFFECTIF,
        })
    return pd.DataFrame(lignes).sort_values("n", ascending=False).reset_index(drop=True)


def resume_loyers_par(df_loyers: pd.DataFrame, colonne: str) -> pd.DataFrame:
    lignes = []
    for cle, groupe in df_loyers.groupby(colonne):
        lignes.append({colonne: cle, "n": len(groupe),
                       "loyer_median": float(np.median(groupe["prix"])),
                       "loyer_moyen": float(np.mean(groupe["prix"])),
                       "effectif_fiable": len(groupe) >= MIN_EFFECTIF})
    return pd.DataFrame(lignes).sort_values("n", ascending=False).reset_index(drop=True)