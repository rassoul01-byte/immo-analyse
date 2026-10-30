import hashlib
import json
from datetime import date
from pathlib import Path

from src.config import RACINE
from src.main import executer

DATE = date(2026, 10, 29)


def empreintes(dossier: Path) -> dict:
    return {str(p): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(dossier.rglob("*")) if p.is_file()}


def test_pipeline_complet(tmp_path):
    avant = empreintes(RACINE / "data" / "raw")
    rapport = executer(DATE, racine=tmp_path)

    # 1. les données brutes ne sont pas modifiées
    assert empreintes(RACINE / "data" / "raw") == avant

    # 2. aucun enregistrement perdu ni compté deux fois
    e = rapport["enregistrements"]
    total = (e["entierement_conformes"] + e["conserves_avec_avertissement"]
             + e["quarantaine"] + e["doublons_ecartes"])
    assert total == rapport["total_recus"] == 3184

    # 3. fichiers produits et cohérents avec le rapport
    propres = json.loads((tmp_path / "data/processed/biens_propres.json").read_text(encoding="utf-8"))
    rejetes = json.loads((tmp_path / "data/quarantine/quarantaine.json").read_text(encoding="utf-8"))
    assert len(propres) == e["entierement_conformes"] + e["conserves_avec_avertissement"]
    assert len(rejetes) == e["quarantaine"] + e["doublons_ecartes"]
    assert all(r["motifs"] for r in rejetes)                     # chaque rejet a un motif
    assert len({r["id_bien"] for r in propres}) == len(propres)  # id_bien unique
    assert (tmp_path / "reports/quality_report.json").exists()
    assert (tmp_path / "reports/quality_summary.csv").exists()


def test_pipeline_idempotent(tmp_path):
    a = executer(DATE, racine=tmp_path)
    contenu_a = (tmp_path / "data/processed/biens_propres.csv").read_bytes()
    b = executer(DATE, racine=tmp_path)
    assert a == b
    assert (tmp_path / "data/processed/biens_propres.csv").read_bytes() == contenu_a