# ImmoAnalyse

Pipeline Python qui transforme des données immobilières **hétérogènes et dégradées** (5 sources, 3 formats) en données **contrôlées, documentées et exploitables**, avec des indicateurs de qualité chiffrés.

Projet fil rouge du **Module 1 : Python pour l'IA et le Machine Learning** (Sonatel Academy / Orange Digital Center).

> **Données synthétiques** inspirées du contexte immobilier sénégalais. Les prix de vente sont des **prix demandés** (annonces), pas des prix de transaction. Aucune conclusion n'est à tirer sur le marché réel.

## Sommaire

1. [Résultats en bref](#résultats-en-bref)
2. [Installation](#installation)
3. [Exécution](#exécution)
4. [Arborescence](#arborescence)
5. [Fonctionnement du pipeline](#fonctionnement-du-pipeline)
6. [Règles métier](#règles-métier)
7. [Stratégies de traitement](#stratégies-de-traitement)
8. [Indicateurs de qualité](#indicateurs-de-qualité)
9. [Fichiers produits](#fichiers-produits)
10. [Décisions documentées](#décisions-documentées)
11. [Limites](#limites)
12. [Pour aller plus loin](#pour-aller-plus-loin)

## Résultats en bref

Exécution du 2026-10-29 sur **3 184 enregistrements reçus** :

| Classement (chaque enregistrement compté une seule fois) | Nombre | Part |
|---|---|---|
| Entièrement conformes | 2 589 | 81,31 % |
| Conservés avec avertissement | 394 | 12,37 % |
| Mis en quarantaine (au moins une règle bloquante violée) | 186 | 5,84 % |
| Doublons exacts écartés | 15 | 0,47 % |

- **2 983 biens** dans les données propres, **201 enregistrements** dans la quarantaine (chacun avec son motif).
- **1 208 enregistrements** ont au moins une valeur corrigée (prix en millions, séparateurs de milliers, virgule décimale, dates `JJ/MM/AAAA`, casse des catégories…). Chaque correction est tracée.
- Séparer ventes et locations est la correction qui pèse le plus : la médiane des prix lue naïvement (59,6 M FCFA) sous-estime d'environ 20 % la médiane des ventes normalisées (75,0 M FCFA).

Le détail se trouve dans `reports/quality_report.json` et dans le notebook `notebooks/01_exploration.ipynb`.

## Installation

Prérequis : **Python 3.10 ou plus récent** (testé avec Python 3.13) et **Git**.

```bash
git clone https://github.com/rassoul01-byte/immo-analyse.git
cd immo-analyse

python -m venv venv
source venv/bin/activate          # Linux / macOS
# venv\Scripts\Activate.ps1       # Windows (PowerShell)

pip install -r requirements.txt
```

Les données brutes (`data/raw/`) sont incluses dans le dépôt : aucun téléchargement supplémentaire n'est nécessaire.

## Exécution

Toutes les commandes se lancent **depuis la racine du projet**, avec l'environnement virtuel activé.

| Objectif | Commande |
|---|---|
| Lancer le pipeline complet | `python -m src.main` |
| Idem, avec une date d'exécution fixée (reproductible) | `python -m src.main --date 2026-10-29` |
| Lancer les tests | `python -m pytest -q tests` |
| Calculer les analyses (statistiques, prix au m², par type et par ville) | `python -m scripts.analyser` |
| Ouvrir le notebook d'exploration | ouvrir `notebooks/01_exploration.ipynb` dans VS Code ou Jupyter, puis « Run All » (après avoir lancé le pipeline) |

Sortie attendue de `python -m src.main --date 2026-10-29` :

```
Enregistrements reçus : 3184
  entièrement conformes : 2589
  conservés avec avertissement : 394
  mis en quarantaine : 186
  doublons écartés : 15
Taux global entièrement conformes : 81.31 %
```

Le pipeline est **idempotent** : le relancer remplace les fichiers de sortie par des fichiers identiques, sans créer de doublon. Les fichiers de `data/raw/` ne sont **jamais modifiés** (vérifié par empreintes dans les tests).

La règle « date non future » dépend de la date d'exécution ; l'option `--date` permet de retrouver exactement les résultats ci-dessus.

## Arborescence

```
immo-analyse/
├── config/
│   └── regles.json                 # seuils, listes autorisées, synonymes, tolérances
├── data/
│   ├── raw/immoanalyse_dataset/    # sources et référentiels (jamais modifiés)
│   ├── processed/                  # biens_propres.csv / .json
│   └── quarantine/                 # quarantaine.csv / .json (avec motifs)
├── docs/
│   ├── decisions.md                # registre de toutes les décisions de nettoyage
│   ├── sources.md                  # description des 5 sources
│   ├── schema_commun.md            # correspondance des colonnes
│   └── inventaire_anomalies.md     # état des données brutes en chiffres
├── notebooks/
│   └── 01_exploration.ipynb        # exploration, qualité, conclusions
├── reports/                        # rapport de qualité et journaux
├── scripts/                        # scripts d'inspection, d'inventaire et d'analyse
├── src/
│   ├── config.py                   # lecture de config/regles.json
│   ├── main.py                     # point d'entrée du pipeline
│   ├── loaders/                    # lecture CSV, Excel, JSON et harmonisation
│   ├── processing/                 # normalisation, type de transaction, export
│   ├── validation/                 # classe Regle, règles métier, moteur, doublons
│   └── analysis/                   # statistiques et rapport de qualité
├── tests/                          # tests unitaires et test de bout en bout
├── requirements.txt
└── README.md
```

## Fonctionnement du pipeline

```
 5 sources brutes (CSV, Excel, JSON)
        │  chargement en texte + colonne de provenance
        ▼
 schéma commun (12 colonnes + 6 additionnelles)         src/loaders/
        │  normalisation + journal de chaque correction
        ▼
 valeurs normalisées (prix, surface, date, catégories)  src/processing/
        │  déduction du type de transaction (vente / location)
        ▼
 15 règles métier (7 bloquantes, 8 avertissements)      src/validation/
        │  détection des doublons exacts, probables, conflits
        ▼
 classement : conforme / avertissement / quarantaine / doublon écarté
        │
        ▼
 exports + rapport de qualité JSON et CSV               data/, reports/
```

Les 5 sources :

| Source | Format | Lignes | Particularités |
|---|---|---|---|
| `plateforme_immo_sn.csv` | CSV `;` | 875 | prix en texte (`57.62 millions`), ventes et locations mélangées |
| `agence_teranga.xlsx` | Excel | 640 | feuille `Annonces` ; la feuille `Params` ne contient que des métadonnées |
| `particuliers.json` | JSON imbriqué | 731 | beaucoup de valeurs manquantes, dates mixtes |
| `notaires.csv` | CSV `,` | 410 | source la plus propre |
| `import_historique.csv` | CSV `;` latin-1 | 528 | encodage, casse variable, formats anciens |

Aucun identifiant n'est universel : le rapprochement se fait sur des attributs métier, jamais sur l'identifiant seul. Voir `docs/sources.md` et `docs/schema_commun.md`.

## Règles métier

Les seuils sont **configurables** dans `config/regles.json`, jamais écrits dans les fonctions. Ce sont des hypothèses pédagogiques, pas des normes de marché.

**Règles bloquantes** (violation : mise en quarantaine) :

| Code | Règle |
|---|---|
| B01 | Identifiant local présent |
| B02 | Type de transaction interprétable (vente ou location) |
| B03 | Prix numérique strictement positif |
| B04 | Surface numérique strictement positive |
| B05 | Date interprétable |
| B06 | Date non future par rapport à la date d'exécution |
| B07 | Type de bien dans le référentiel (7 catégories) |

**Règles d'avertissement** (violation : bien conservé, anomalie signalée dans la colonne `avertissements`) :

| Code | Règle | Seuil |
|---|---|---|
| A01 | Surface non atypique | 5 à 2 000 m² |
| A02 | Prix de vente non atypique | 100 000 à 2 000 000 000 FCFA |
| A03 | Loyer mensuel non atypique | 25 000 à 5 000 000 FCFA |
| A04 | Prix au m² dans la fourchette du type de bien | référentiel des catégories |
| A05 | Nombre de chambres plausible | au plus 10 pour un appartement ou un studio |
| A06 | Salles de bain ≤ chambres + 2 | marge de 2 |
| A07 | Ville cohérente avec la région | référentiel géographique |
| A08 | Périodicité du loyer renseignée | pour les locations |

Chaque règle répond **conforme**, **non conforme** ou **non évaluable**. Un enregistrement non évaluable n'est jamais compté comme conforme.

## Stratégies de traitement

- **Normaliser sans deviner.** Un prix `57.62 millions`, `438 746 000` ou `65575000 FCFA` est corrigé avec un motif ; `à négocier` est invalide ; `None FCFA` est une valeur manquante déguisée. Une surface `1,250` est **ambiguë** (milliers ou décimale) et n'est jamais convertie par défaut.
- **Dates.** Les dates `JJ/MM/AAAA` sont lues avec la convention de la source, **prouvée** par les données (des premiers nombres supérieurs à 12 et jamais de second nombre supérieur à 12). Les dates impossibles (`32/13/2024`) sont invalides.
- **Type de transaction** (vente ou location), absent de trois sources : déduit dans cet ordre, valeur fournie, nature de la source (notaires et historique = ventes), statut contrôlé par le prix, puis échelle de prix (seuil à 2 000 000 FCFA, loyers au plus 1,76 M et ventes au moins 5,16 M dans les sources étiquetées). En cas de contradiction ou d'absence de preuve : ambigu, mise en quarantaine.
- **Doublons.** Doublon exact : même source, même identifiant, mêmes valeurs ; la copie est écartée. Doublons probables et conflits (surface à ±0,2 %, date à ±30 jours, prix à ±5 %, chambres compatibles) : signalés, **jamais fusionnés**. Résultat sur ce pack : 15 doublons exacts, aucun doublon probable.
- **Quarantaine.** Chaque enregistrement rejeté est conservé avec son motif et ses valeurs brutes (`data/quarantine/`).
- **Données brutes.** Intactes ; toutes les opérations se font sur des copies en mémoire, les résultats sont écrits dans `data/processed/`, `data/quarantine/` et `reports/`.

## Indicateurs de qualité

Calculés par le pipeline et écrits dans `reports/quality_report.json` (détail) et `reports/quality_summary.csv` (version à plat) :

- nombre total d'enregistrements reçus, par source ;
- valeurs manquantes par colonne et par source, avec les colonnes **absentes par construction** distinguées des valeurs manquantes ;
- nombre et taux de doublons exacts ;
- erreurs de conversion par champ ;
- pour chaque règle : conformes, non conformes, non évaluables, dénominateur et taux de conformité ;
- enregistrements corrigés, mis en quarantaine, conservés avec avertissement, entièrement conformes.

**Définitions.**

- Taux de conformité d'une règle = conformes ÷ évaluables × 100. Les non évaluables sont comptés à part.
- Taux global = enregistrements entièrement conformes ÷ total reçu. Chaque enregistrement est compté **une seule fois** : doublon écarté, sinon quarantaine, sinon avertissement, sinon entièrement conforme.
- Enregistrement corrigé : au moins une valeur normalisée. Les types de transaction et périodicités déduits sont comptés à part.

## Fichiers produits

| Fichier | Contenu |
|---|---|
| `data/processed/biens_propres.csv` / `.json` | 2 983 biens, avec la colonne `avertissements` et un `id_bien` unique |
| `data/quarantine/quarantaine.csv` / `.json` | 201 enregistrements rejetés avec motifs et valeurs brutes |
| `reports/quality_report.json` | rapport de qualité complet |
| `reports/quality_summary.csv` | indicateurs à plat |
| `reports/journal_normalisation.csv` | chaque correction ou anomalie (valeur brute, valeur normalisée, motif) |
| `reports/violations.csv` | chaque règle violée par enregistrement |
| `reports/liens_doublons.csv` | doublons et conflits détectés |
| `reports/analyses/` | statistiques de vente, résumés par type de bien et par ville, loyers |

## Décisions documentées

Chaque choix de nettoyage, y compris les décisions de **ne pas corriger**, est justifié dans [`docs/decisions.md`](docs/decisions.md) : convention de dates par source, `pieces` non assimilé à `chambres`, définition d'une valeur vide, déduction du type de transaction, seuils des doublons et leur justification chiffrée, définitions des indicateurs, conventions d'analyse.

## Limites

- Données synthétiques : aucun résultat ne décrit le marché réel ; les différences entre villes sont à interpréter avec prudence.
- Prix de vente = prix demandés, pas prix de transaction conclue.
- Les seuils de plausibilité sont des hypothèses pédagogiques.
- La déduction du type de transaction s'appuie sur les échelles de prix observées dans ce pack ; elle ne se généralise pas sans vérification.
- Aucun doublon probable détecté entre sources avec les critères retenus, alors que le cahier des charges évoque des chevauchements ; le détecteur est validé sur des cas fabriqués.
- Seuls 171 loyers sur 452 sont analysables (périodicité mensuelle connue) : la périodicité n'est jamais devinée.
- La règle B06 dépend de la date d'exécution.

## Pour aller plus loin

Extensions possibles : rapprochement approfondi des doublons entre sources, règles dans un fichier de configuration par règle, registre de sources (YAML), ingestion Parquet ou API locale, journalisation avec `logging`, jeu de données documenté pour un futur modèle de prédiction.

## Auteur

Seydina Wade, DEV DATA P8, Sonatel Academy / Orange Digital Center.