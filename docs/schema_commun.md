# Schéma commun et correspondance des colonnes

Implémenté dans `src/loaders/harmonisation.py`.

| Schéma commun | plateforme | teranga | particuliers | notaires | historique |
|---|---|---|---|---|---|
| id_local | ref_plateforme | Code | annonce.id | id_acte | ID |
| date | date_mise_en_ligne | Date | annonce.date | date_acte | DateVente |
| type_transaction | type_transaction | (absente) | annonce.details.transaction | (absente) | (absente) |
| type_bien | categorie | Type | annonce.details.type | type_bien | TypeBien |
| region | region | Region | annonce.localisation.region | region | Region |
| ville | commune | Ville | annonce.localisation.ville | ville | Ville |
| prix | prix | Prix_FCFA | annonce.details.prix | montant_fcfa | Prix |
| surface | surface | Surface_m2 | annonce.details.surface | superficie | Surface |
| chambres | (non mappé, voir D-003) | Chambres | annonce.details.chambres | nb_chambres | Chambres |
| salles_bain | sdb | SDB | annonce.details.sdb | (absente) | SallesBain |
| statut | statut | Statut | annonce.statut | statut | (absente) |

## Colonnes additionnelles (conservées, propres à certaines sources)
`quartier`, `devise`, `description`, `date_expiration` (plateforme), `commercial` (teranga), `pieces` (plateforme).

## Convention
Une colonne absente d'une source est remplie avec une valeur manquante (`NA`). Elle est considérée comme **non évaluable**, et non comme conforme ou non conforme.
