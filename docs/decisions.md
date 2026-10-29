# Registre des décisions de nettoyage

## D-001 — Convention de dates de la source historique
- **Constat** : 215 dates au format `xx/xx/xxxx` dans `import_historique.csv`.
- **Preuve** : 127 ont un premier nombre > 12, aucune n'a de second nombre > 12.
- **Décision** : interprétation `JJ/MM/AAAA` pour toute la source.
- **Limite** : 88 dates sont ambiguës isolément ; elles sont converties par cohérence de source.
- **Script** : `scripts/inspection_dates.py`

## D-002 — Convention de dates de la source particuliers
- **Constat** : 446 dates au format `xx/xx/xxxx` et 285 au format ISO dans `particuliers.json`.
- **Preuve** : sur les 446 dates à barres, 269 ont un premier nombre > 12 et aucune n'a de second nombre > 12.
- **Décision** : interprétation `JJ/MM/AAAA` pour les dates à barres de cette source.
- **Limite** : 177 dates sont ambiguës isolément (jour et mois ≤ 12) ; elles sont converties par cohérence de source.
- **Script** : à reproduire avec la méthode de `scripts/inspection_dates.py`.

## D-003 — `pieces` non assimilé à `chambres`
- **Constat** : la plateforme fournit `pieces`, les autres sources `chambres`.
- **Décision** : `pieces` conservé dans une colonne additionnelle ; `chambres` reste non renseigné pour la plateforme.
- **Raison** : le nombre de pièces inclut le salon ; l'assimiler fausserait les règles sur les chambres et les salles de bain.

## D-004 — `type_transaction` non déduit pour teranga, notaires, historique
- **Constat** : colonne absente de ces trois sources (1 578 enregistrements) et le pack ne précise rien.
- **Décision** : laissé non renseigné à l'harmonisation ; à trancher à l'étape de normalisation, avec justification.

## D-005 — Définition d'une valeur « vide »
- **Décision** : une valeur est considérée vide si elle est absente, vide ou égale à un marqueur de la constante `VALEURS_VIDES` (`nan`, `none`, `null`, `n/a`, `na`, `-`, `inconnu`).
- **Limite** : des marqueurs combinés à une unité (par exemple `None FCFA` dans `particuliers`, 2 cas) ne sont pas détectés par cette liste ; ils sont comptés comme « non convertibles » et seront traités à l'étape de nettoyage.

## D-006 — Doublons exacts de la plateforme
- **Constat** : 15 paires d'enregistrements identiques (même `id_local`, mêmes valeurs sur tous les autres champs), toutes dans la plateforme.
- **Décision prévue** : conserver la première occurrence et journaliser la seconde comme doublon exact ; les conflits (même identifiant, valeurs différentes) seront signalés et non résolus arbitrairement.


## D-007 — Règles et seuils externalisés dans config/regles.json
- **Décision** : seuils, listes autorisées, synonymes et fourchettes sont lus depuis `config/regles.json`, jamais écrits dans les fonctions.
- **Raison** : exigence du cahier des charges (seuils configurables) ; permet de modifier une règle sans toucher au code.
- **Limite** : les seuils sont des hypothèses pédagogiques, pas des normes officielles.


## D-008 — Convention de dates des sources teranga et notaires
- **Constat** : teranga contient 298 dates à barres, notaires en contient 6.
- **Preuve teranga** : 181 ont un premier nombre > 12, aucune n'a de second nombre > 12 ; 117 sont ambiguës isolément. Convention `JJ/MM/AAAA`.
- **Notaires** : les 6 dates à barres sont toutes impossibles (`32/13/2024`) ; elles sont invalides et iront en quarantaine.
- **Décision** : `JJ/MM/AAAA` appliqué à toutes les sources, validé par les preuves de D-001, D-002 et D-008.

## D-009 — Type de bien hors référentiel : gravité à trancher
- **Constat** : le cahier des charges (6.1) prescrit la quarantaine, `regles_metier.md` prescrit un avertissement.
- **Décision** : à fixer dans `config/regles.json` à la tâche 3. Dans ce pack, aucun cas n'est concerné (tous les types se ramènent aux 7 catégories).

## D-010 — Nombres en lettres et ambiguïté « 1,250 »
- **Décision** : seul le nombre écrit en lettres du dictionnaire (`quatre-vingt`, 4 cas) est converti, avec motif. Une surface de la forme `x,yyy` est marquée ambiguë et jamais convertie par défaut.
- **Limite** : le cas `x,yyy` n'apparaît pas dans ce pack ; il est couvert par un test.