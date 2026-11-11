"""Gegenprobe der Stabilität (nicht Teil der Tests): dieselben Messreihen auf anderen festen Graphen (Seeds 700 bis 709 statt 600 bis 609).

Aufruf (aus dem Repo-Ordner, mit dem Test-venv; braucht OR-Tools für die Optima der neuen Graphen):
    python tools/gegenprobe.py

Gemessen werden die Zellen `ZELLEN` (Sinz-Zähler und Totalizer, Budget 300.000 Konflikte); das Optimum je Graph bestimmt OR-Tools CP-SAT wie in `tools/optima.py`.
Die Ausgabe (Median, Maximum, Zählung je Graph) steht in der README unter „Stabilität“; die Zahlen sind eine Messung dieses Skripts, kein Test.
"""

import statistics
import sys
from pathlib import Path

HIER = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HIER))
sys.path.insert(0, str(HIER / "tools"))

import kkd_algorithm as A  # noqa: E402
import kkd_constants as C  # noqa: E402
from optima import optimum_cpsat  # noqa: E402

SEEDS = tuple(range(700, 710))
ZELLEN = ((25, 3.0, 0), (40, 3.0, 0), (40, 3.0, -1), (50, 3.0, 0), (50, 3.0, -1))      # (n, Grad, Abstand zum Optimum)
BUDGET = C.BUDGET_REFERENZ


def main() -> None:
    for n, grad, delta in ZELLEN:
        je = {v: [] for v in ("sinz", "totalizer")}
        for seed in SEEDS:
            kanten = A.graph(n, grad, seed)
            k = optimum_cpsat(n, kanten) + delta
            for v in je:
                r = A.messe_lauf(n, kanten, k, v, BUDGET)
                assert r["antwort"] is (delta == 0), (n, grad, delta, seed, v)
                je[v].append(r["konflikte"])
        weniger = sum(t < s for s, t in zip(je["sinz"], je["totalizer"]))
        gleich = sum(t == s for s, t in zip(je["sinz"], je["totalizer"]))
        ms, mt = statistics.median(je["sinz"]), statistics.median(je["totalizer"])
        print(f"n = {n}, Grad {grad}, k = Optimum{delta:+d}: Sinz Median {ms} (Max {max(je['sinz'])}), Totalizer Median {mt} (Max {max(je['totalizer'])}), "
              f"Verhältnis Sinz/Totalizer {ms / mt:.2f}; Totalizer weniger in {weniger}, gleich in {gleich}, mehr in {10 - weniger - gleich} von 10", flush=True)


if __name__ == "__main__":
    main()
