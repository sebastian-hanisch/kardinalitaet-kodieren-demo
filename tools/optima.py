"""Messskript der eingefrorenen Optima: schreibt `kkd_optima.json` (kleinstes Vertex Cover der festen Konfliktgraphen).

Aufruf (aus dem Repo-Ordner, mit dem Test-venv; braucht OR-Tools, nur hier und in den Tests, nie in der App):
    python tools/optima.py

Die Graphen sind `kkd_algorithm.graph(n, grad, seed)` für n in `E3_N`, Grad in `E3_GRAD` und die zehn Seeds `GRAPH_SEEDS`. Das Optimum bestimmt OR-Tools CP-SAT
(ein Arbeiter, Minimierung der Zahl der Kontrollpunkte unter „jede Kante an mindestens einem Ende kontrolliert“); die Tests prüfen es gegen Aufzählung
(n bis 20, eigene Graphen) und gegen eine zweite CP-SAT-Rechnung mit `Sum <= k`.
"""

import json
import sys
from pathlib import Path

from ortools.sat.python import cp_model

HIER = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HIER))

import kkd_algorithm as A  # noqa: E402
import kkd_constants as C  # noqa: E402


def optimum_cpsat(n: int, kanten) -> int:
    m = cp_model.CpModel()
    x = [m.NewBoolVar(f"x{i}") for i in range(n)]
    for a, b in kanten:
        m.AddBoolOr([x[a], x[b]])
    m.Minimize(sum(x))
    s = cp_model.CpSolver()
    s.parameters.num_workers = 1
    status = s.Solve(m)
    assert status == cp_model.OPTIMAL
    return int(round(s.ObjectiveValue()))


def main() -> None:
    optima = {}
    for n in C.E3_N:
        for grad in C.E3_GRAD:
            optima[f"{n}|{grad}"] = [optimum_cpsat(n, A.graph(n, grad, seed)) for seed in C.GRAPH_SEEDS]
            print(n, grad, optima[f"{n}|{grad}"], flush=True)
    zeilen = ['{', f'"version": 1, "seeds": {json.dumps(list(C.GRAPH_SEEDS))}, "optima": {{']
    zeilen += [f'"{k}": {json.dumps(v)}' + ("," if i < len(optima) - 1 else "") for i, (k, v) in enumerate(optima.items())]
    zeilen += ['}', '}']
    (HIER / C.OPTIMA_DATEI).write_text("\n".join(zeilen) + "\n", encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
