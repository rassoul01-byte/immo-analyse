# Description des sources

Pack de données synthétiques (aucune transaction réelle). Volumes comptés sur les fichiers fournis.

| Source | Fichier | Format | Lignes | Particularités constatées |
|---|---|---|---|---|
| plateforme | plateforme_immo_sn.csv | CSV `;` UTF-8 | 875 | Prix en texte (`57.62 millions`, espaces, `à négocier`), surfaces à virgule décimale, variante `appart`, ventes (698) et locations (177) mélangées, devise portant aussi la périodicité (`FCFA/mois`) |
| teranga | agence_teranga.xlsx | Excel | 640 | Feuille `Annonces` = biens ; feuille `Params` = 4 lignes de métadonnées (version, source, date d'export, contact), jamais chargée comme des biens |
| particuliers | particuliers.json | JSON imbriqué | 731 | Structure `annonce > localisation / details`, 61 prix et 75 surfaces manquants, dates mixtes (ISO et JJ/MM/AAAA), valeurs textuelles (`None FCFA`, `quatre-vingt`) |
| notaires | notaires.csv | CSV `,` UTF-8 | 410 | Source la plus propre, 14 montants manquants, pas de `salles_bain` |
| historique | import_historique.csv | CSV `;` latin-1 | 528 | Encodage latin-1, casse variable (`CHAMBRE`, `Chambre`), prix avec espaces, surfaces à virgule, dates mixtes, 8 villes et 10 prix manquants, pas de `statut` |

Total reçu : 3 184 enregistrements.

## Règles de lecture
- Tout est chargé en texte (`dtype=str`) pour ne rien perdre avant la normalisation.
- Les fichiers de `data/raw/` ne sont jamais modifiés.
- Chaque ligne porte sa provenance dans la colonne `source`.
