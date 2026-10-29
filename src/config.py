import json
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
CHEMIN_CONFIG = RACINE / "config" / "regles.json"


def charger_config(chemin: Path = CHEMIN_CONFIG) -> dict:
    with open(chemin, encoding="utf-8") as f:
        return json.load(f)


CONFIG = charger_config()