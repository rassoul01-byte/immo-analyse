# Registre des décisions de nettoyage

## D-001 — Convention de dates de la source historique
- **Constat** : 215 dates au format `xx/xx/xxxx` dans `import_historique.csv`.
- **Preuve** : 127 ont un premier nombre > 12, aucune n'a de second nombre > 12.
- **Décision** : interprétation `JJ/MM/AAAA` pour toute la source.
- **Limite** : 88 dates sont ambiguës isolément ; elles sont converties par cohérence de source.
- **Script** : `scripts/inspection_dates.py`