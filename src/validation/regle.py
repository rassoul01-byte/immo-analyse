"""Brique de base : une règle métier = un nom, une gravité, une fonction de contrôle."""
from dataclasses import dataclass
from typing import Callable

CONFORME = "conforme"
NON_CONFORME = "non_conforme"
NON_EVALUABLE = "non_evaluable"

BLOQUANTE = "bloquante"
AVERTISSEMENT = "avertissement"


@dataclass(frozen=True)
class Verdict:
    etat: str
    motif: str = ""


def conforme() -> Verdict:
    return Verdict(CONFORME)


def non_conforme(motif: str) -> Verdict:
    return Verdict(NON_CONFORME, motif)


def non_evaluable(motif: str = "") -> Verdict:
    return Verdict(NON_EVALUABLE, motif)


@dataclass(frozen=True)
class Regle:
    code: str
    nom: str
    gravite: str
    controle: Callable[[dict], Verdict]

    def evaluer(self, ligne: dict) -> Verdict:
        return self.controle(ligne)
