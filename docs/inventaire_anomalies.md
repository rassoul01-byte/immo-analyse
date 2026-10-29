# Inventaire des anomalies initiales (Étape 3)

Produit par `scripts/inventaire_anomalies.py` sur les données brutes, avant toute correction.
Total reçu : **3 184** enregistrements (plateforme 875, particuliers 731, teranga 640, historique 528, notaires 410).

## Valeurs manquantes (champs communs, hors colonnes absentes par construction)
| Champ | Source | Manquants | Taux sur la source |
|---|---|---|---|
| prix | particuliers | 61 | 8,3 % |
| prix | notaires | 14 | 3,4 % |
| prix | historique | 10 | 1,9 % |
| surface | particuliers | 75 | 10,3 % |
| surface | plateforme | 5 | 0,6 % |
| ville | historique | 8 | 1,5 % |

Champs absents par construction (non évaluables) : `type_transaction` (teranga, notaires, historique : 1 578 enregistrements), `chambres` (plateforme : 875), `salles_bain` (notaires : 410), `statut` (historique : 528).

## Valeurs non convertibles telles quelles en nombre
| Champ | Source | Non convertibles | Évaluables |
|---|---|---|---|
| prix | historique | 72 | 518 |
| prix | plateforme | 71 | 875 |
| prix | particuliers | 7 | 670 |
| surface | historique | 50 | 528 |
| surface | plateforme | 29 | 870 |
| surface | particuliers | 4 | 656 |

« Non convertible telle quelle » ne veut pas dire « erreur » : `57.62 millions` ou `26 620 000` sont normalisables, `à négocier` ne l'est pas. Le tri est fait à l'étape de nettoyage.

## Doublons et identifiants
- Doublons exacts (toutes colonnes identiques hors source) : **15** (0,47 % de 3 184), tous dans la plateforme.
- Identifiants répétés dans une même source : 30 lignes dans la plateforme, soit 15 paires, toutes identiques sur les autres champs.

## Formats de dates
| Source | Formats observés |
|---|---|
| plateforme | ISO uniquement (875) |
| historique | ISO (313), JJ/MM/AAAA (215) |
| particuliers | JJ/MM/AAAA (446), ISO (285) |
