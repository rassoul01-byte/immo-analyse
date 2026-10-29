import pandas as pd
from src.loaders.harmonisation import charger_toutes_les_sources, COLONNES_FINALES

VALEURS_VIDES = {"", "nan", "none", "null", "n/a", "na", "-", "inconnu"}
CHAMPS_NUMERIQUES = ["prix", "surface", "chambres", "salles_bain"]

df = charger_toutes_les_sources()


def est_vide(s):
    return s.isna() | s.astype("string").str.strip().str.lower().isin(VALEURS_VIDES)


# 1. Volumes reçus par source
recus = df["source"].value_counts().rename("recus")

# 2. Valeurs manquantes, par source et par colonne
champs = [c for c in COLONNES_FINALES if c != "source"]
vides = pd.DataFrame({c: est_vide(df[c]) for c in champs})
vides["source"] = df["source"]
manquants = vides.groupby("source").sum().T
print("=== Reçus ===\n", recus)
print("\n=== Manquants (comptes) ===\n", manquants)

# 3. Erreurs de conversion numérique (valeur non vide, non convertible telle quelle)
lignes = []
for champ in CHAMPS_NUMERIQUES:
    for src, sous in df.groupby("source"):
        brut = sous[champ][~est_vide(sous[champ])].astype(str)
        echecs = pd.to_numeric(brut, errors="coerce").isna().sum()
        lignes.append({"source": src, "champ": champ,
                       "evaluables": len(brut), "non_convertibles": int(echecs)})
conv = pd.DataFrame(lignes)
print("\n=== Conversions numériques ===\n", conv[conv.non_convertibles > 0])

# 4. Doublons exacts (toutes colonnes identiques, hors source)
cols_sans_source = [c for c in COLONNES_FINALES if c != "source"]
dup_exacts = df.duplicated(subset=cols_sans_source, keep="first")
print("\n=== Doublons exacts ===", int(dup_exacts.sum()),
      f"({dup_exacts.mean():.2%} de {len(df)})")

# 5. Identifiants répétés à l'intérieur d'une même source
rep = df.groupby("source")["id_local"].apply(lambda s: int(s.duplicated(keep=False).sum()))
print("\n=== Lignes dont l'id_local est répété dans la même source ===\n", rep)

# 6. Export dans reports/
manquants.to_csv("reports/inventaire_manquants.csv")
conv.to_csv("reports/inventaire_conversions.csv", index=False)