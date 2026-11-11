"""Messskript der vorgerechneten Messreihen von Experiment 3: schreibt `kkd_messungen.json` (Konflikte je Graph und Kodierung, Antwort, Klauseln, Hilfsvariablen).

Aufruf (aus dem Repo-Ordner, mit dem Test- oder Runtime-venv):
    python tools/messungen.py --teil 0 2 --out teil_a.json       # die Zellen mit Nummer 0, 2, ... aus REFERENZ_ZELLEN messen
    python tools/messungen.py --zusammenfuegen teil_a.json teil_b.json   # Teile zu kkd_messungen.json vereinen
    python tools/messungen.py --alle                             # alle Zellen, direkt nach kkd_messungen.json
    python tools/messungen.py --liste                            # Nummern und Zellen anzeigen

Gemessen wird mit denselben Funktionen wie in der Live-Messreihe der App (`kkd_evaluation.messe_zelle`), Budget `BUDGET_REFERENZ`.
Aufwand wird in Konflikten gezählt, nie in Sekunden; die Laufzeit des Skripts ist kein Messwert.
"""

import argparse
import json
import sys
from pathlib import Path

HIER = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HIER))

import kkd_constants as C  # noqa: E402
import kkd_evaluation as E  # noqa: E402


def schreibe(daten: dict, ziel: Path) -> None:
    """Eine Zelle je Zeile (gut zu vergleichen)."""
    zeilen = ['{', f'"version": 1, "budget": {C.BUDGET_REFERENZ}, "graph_seeds": {json.dumps(list(C.GRAPH_SEEDS))},', '"zellen": {']
    schluessel = list(daten["zellen"])
    for i, k in enumerate(schluessel):
        zeilen.append(f'"{k}": {json.dumps(daten["zellen"][k], ensure_ascii=False, separators=(",", ":"))}' + ("," if i < len(schluessel) - 1 else ""))
    zeilen += ['}', '}']
    ziel.write_text("\n".join(zeilen) + "\n", encoding="utf-8", newline="\n")


def messe(nummern) -> dict:
    zellen = {}
    for i in nummern:
        n, grad, modus, k = C.REFERENZ_ZELLEN[i]
        zellen[E.zellen_schluessel(n, grad, modus, k)] = E.messe_zelle(n, grad, modus, k, C.VERFAHREN, C.BUDGET_REFERENZ)
        print(i, n, grad, modus, k, flush=True)
    return {"zellen": zellen}


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--teil", type=int, nargs="*")
    p.add_argument("--out", type=Path)
    p.add_argument("--zusammenfuegen", type=Path, nargs="*")
    p.add_argument("--alle", action="store_true")
    p.add_argument("--liste", action="store_true")
    a = p.parse_args()
    if a.liste:
        for i, z in enumerate(C.REFERENZ_ZELLEN):
            print(i, z)
    elif a.zusammenfuegen:
        zellen = {}
        for pfad in a.zusammenfuegen:
            zellen.update(json.loads(pfad.read_text(encoding="utf-8"))["zellen"])
        ordnung = [E.zellen_schluessel(*z) for z in C.REFERENZ_ZELLEN]
        schreibe({"zellen": {k: zellen[k] for k in ordnung if k in zellen}}, HIER / C.MESSUNGEN_DATEI)
    elif a.alle:
        schreibe(messe(range(len(C.REFERENZ_ZELLEN))), HIER / C.MESSUNGEN_DATEI)
    elif a.teil is not None and a.out:
        a.out.write_text(json.dumps(messe(a.teil), ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
