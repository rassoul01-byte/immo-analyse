"""Applique les règles, calcule les taux de conformité et classe les enregistrements."""
import pandas as pd

from src.validation.regle import (
    AVERTISSEMENT, BLOQUANTE, CONFORME, NON_CONFORME, NON_EVALUABLE,
)

QUARANTAINE = "quarantaine"
AVEC_AVERTISSEMENT = "conserve_avec_avertissement"
CONFORME_TOTAL = "entierement_conforme"


def appliquer_regles(df_norm: pd.DataFrame, regles: list):
    """Renvoie (violations, rapport).

    violations : une ligne par (enregistrement, règle) non conforme
    rapport    : une ligne par règle, avec le dénominateur des évaluables
    """
    violations, comptes = [], {r.code: {CONFORME: 0, NON_CONFORME: 0, NON_EVALUABLE: 0}
                               for r in regles}
    for ligne in df_norm.to_dict("records"):
        for regle in regles:
            verdict = regle.evaluer(ligne)
            comptes[regle.code][verdict.etat] += 1
            if verdict.etat == NON_CONFORME:
                violations.append({"id_ligne": ligne["id_ligne"], "source": ligne["source"],
                                   "code": regle.code, "gravite": regle.gravite,
                                   "motif": verdict.motif})

    lignes = []
    for regle in regles:
        c = comptes[regle.code]
        evaluables = c[CONFORME] + c[NON_CONFORME]
        lignes.append({
            "code": regle.code, "regle": regle.nom, "gravite": regle.gravite,
            "evaluables": evaluables, "conformes": c[CONFORME],
            "non_conformes": c[NON_CONFORME], "non_evaluables": c[NON_EVALUABLE],
            "taux_conformite": round(100 * c[CONFORME] / evaluables, 2) if evaluables else None,
        })
    return pd.DataFrame(violations), pd.DataFrame(lignes)


def classer(df_norm: pd.DataFrame, violations: pd.DataFrame) -> pd.DataFrame:
    """Un enregistrement est compté une seule fois, dans une seule catégorie."""
    bloques = set(violations.loc[violations["gravite"] == BLOQUANTE, "id_ligne"])
    avertis = set(violations.loc[violations["gravite"] == AVERTISSEMENT, "id_ligne"])

    def categorie(i):
        if i in bloques:
            return QUARANTAINE
        if i in avertis:
            return AVEC_AVERTISSEMENT
        return CONFORME_TOTAL

    out = df_norm.copy()
    out["classement"] = out["id_ligne"].map(categorie)
    return out
