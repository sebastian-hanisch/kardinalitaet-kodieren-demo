"""Einheiten der Demo „Kardinalität kodieren“ (Standardbibliothek; die Kodierungen selbst stehen in der Kern-Kopie `kkd_kodierung`).

Jede Einheit ist einzeln aufrufbar und getestet (Handrechnung in `tests/test_algorithm.py`, unabhängige Rechenwege in `tests/test_oracle_kardinalitaet_kodieren.py`):

  `kodierung`                 „höchstens k von n“ in einer der drei Kodierungen, mit lesbaren Namen der Hilfsvariablen und einer Gruppe je Klausel
  `klauselzahl`, `hilfsvariablen`   Formeln für die Wachstumsansicht ohne Bau (Totalizer: Rekursion über die Blattzahlen)
  `Propagator`, `propagiere`  Einheitspropagation mit auslösender Klausel je Literal
  `erfuellbar`, `semantik_pruefen`  Aufzählung aller Eingaben mit existenzieller Prüfung der Hilfsvariablen
  `vollstaendigkeit`          zählt übersehene erzwungene Eingänge und übersehene Verletzungen der Einheitspropagation
  `kontrollpunkte`            Vertex Cover höchstens k als Formel (Kantenklauseln plus Zähler)
  `optimum_aufzaehlung`, `optimum`  kleinstes Vertex Cover (Aufzählung bzw. eingefrorene Datei)
  `messe_lauf`                ein Löserlauf: Klauseln, Hilfsvariablen, Konflikte, Antwort, Modellprüfung

Aufwand wird in Konflikten gezählt, nie in Sekunden.
"""

import itertools
import json
from collections import deque
from math import comb
from pathlib import Path
from typing import NamedTuple

import kkd_constants as C
import kkd_instanzen as I
import kkd_kodierung as K
from kkd_cdcl import solve
from kkd_rng import SplitMix64

HIER = Path(__file__).resolve().parent

# --------------------------------------------------------------------------------------------------------------- Kodierungen mit Namen


class Kodierung(NamedTuple):
    verfahren: str
    n: int
    k: int
    klauseln: list         # Tupel von Literalen; Eingänge 1..n, Hilfsvariablen n+1..n_gesamt
    n_gesamt: int
    namen: dict            # Variable -> lesbarer Name (x1.., s11.., oL1..)
    gruppen: list          # je Klausel eine Bezeichnung der Herkunft


def literal_text(lit: int, namen: dict) -> str:
    name = namen.get(abs(lit), f"x{abs(lit)}")
    return name if lit > 0 else "¬" + name


def klausel_text(klausel, namen: dict) -> str:
    return "(" + " ∨ ".join(literal_text(l, namen) for l in klausel) + ")" if klausel else "()"


def _seitenname(tag: str) -> str:
    return "-".join({"L": "links", "R": "rechts"}[c] for c in tag)


def _sinz_namen_gruppen(n: int, k: int):
    """Namen s_ij (i = 1..n-1 Eingänge, j = 1..k) in der Reihenfolge der Vergabe und die Gruppe je Klausel (Reihenfolge des Aufbaus)."""
    klein = max(n - 1, k) < 10
    namen = {}
    for i in range(1, n):
        for j in range(1, k + 1):
            namen[n + (i - 1) * k + j] = f"s{i}{j}" if klein else f"s{i},{j}"
    gruppen = ["Eingang 1"] * k                                  # (¬x1 ∨ s11) und (¬s1j) für j = 2..k
    for i in range(2, n):
        gruppen += [f"Eingang {i}"] * (2 + 2 * (k - 1) + 1)      # Zeile i: 2 + 2(k-1) + 1 Klauseln
    gruppen.append(f"Eingang {n}")
    return namen, gruppen


def _totalizer_namen_gruppen(n: int, k: int):
    """Namen o_t je Knoten (Wurzel W, Kinder L und R, darunter LL, LR, ...) in der Reihenfolge der Vergabe (Nachordnung) und die Gruppe je Klausel."""
    namen, gruppen = {}, []
    zaehler = [n]

    def rec(m: int, tag: str):
        """Gibt die Zahl der Ausgänge des Knotens zurück."""
        if m == 1:
            return 1
        mitte = m // 2
        oa = rec(mitte, tag + "L")
        ob = rec(m - mitte, tag + "R")
        o = min(k + 1, oa + ob)
        for t in range(1, o + 1):
            zaehler[0] += 1
            namen[zaehler[0]] = f"o{tag or 'W'}{t}"
        gruppen.extend([("Wurzel" if not tag else f"Addierer {_seitenname(tag)}")] * ((oa + 1) * (ob + 1) - 1))
        return o

    if rec(n, "") > k:
        gruppen.append("Schranke")
    return namen, gruppen


def kodierung(n: int, k: int, verfahren: str) -> Kodierung:
    """„Höchstens k der Eingänge x1..xn sind wahr“ als Klauseln (Kern-Kodierung) samt Namen und Gruppen. k >= n ergibt keine Klausel."""
    if verfahren not in K.VERFAHREN:
        raise ValueError(f"unbekannte Kodierung {verfahren!r}")
    if n < 1 or k < 0:
        raise ValueError("n >= 1 und k >= 0 verlangt")
    pool = K.Hilfsvariablen(n)
    klauseln = K.hoechstens(list(range(1, n + 1)), k, pool, verfahren)
    namen = {i: f"x{i}" for i in range(1, n + 1)}
    if k >= n:
        gruppen = []
    elif verfahren == "binomial":
        gruppen = ["verbotene Teilmenge"] * len(klauseln)
    elif k == 0:
        gruppen = ["Einheitsklausel"] * len(klauseln)
    else:
        hilf, gruppen = (_sinz_namen_gruppen if verfahren == "sinz" else _totalizer_namen_gruppen)(n, k)
        namen.update(hilf)
    if k == 0 and k < n:
        gruppen = ["Einheitsklausel"] * len(klauseln)
    assert len(gruppen) == len(klauseln) and pool.n - n == len(namen) - n, (verfahren, n, k)
    return Kodierung(verfahren, n, k, klauseln, pool.n, namen, gruppen)


def klauselzahl(verfahren: str, n: int, k: int) -> int:
    """Klauseln der Kodierung ohne Aufbau: binomial C(n, k+1), Sinz 2nk + n − 3k − 1, Totalizer per Rekursion."""
    return _zahlen(verfahren, n, k)[0]


def hilfsvariablen(verfahren: str, n: int, k: int) -> int:
    """Hilfsvariablen der Kodierung ohne Aufbau: binomial 0, Sinz (n − 1)k, Totalizer per Rekursion."""
    return _zahlen(verfahren, n, k)[1]


def _zahlen(verfahren: str, n: int, k: int) -> tuple[int, int]:
    if k >= n:
        return 0, 0
    if k == 0:
        return n, 0
    if verfahren == "binomial":
        return comb(n, k + 1), 0
    if verfahren == "sinz":
        return K.klauselzahl_sinz(n, k), (n - 1) * k
    if verfahren == "totalizer":
        def rec(m: int):
            if m == 1:
                return 1, 0, 0                       # Ausgänge, Klauseln, Hilfsvariablen (ein Blatt ist der Eingang selbst)
            a = m // 2
            oa, ca, ha = rec(a)
            ob, cb, hb = rec(m - a)
            o = min(k + 1, oa + ob)
            return o, ca + cb + (oa + 1) * (ob + 1) - 1, ha + hb + o

        o, c, h = rec(n)
        return c + (1 if o > k else 0), h
    raise ValueError(f"unbekannte Kodierung {verfahren!r}")


# ----------------------------------------------------------------------------------------------------------------- Einheitspropagation


class Prop(NamedTuple):
    belegung: dict         # Variable -> bool nach der Propagation (bis zum Konflikt)
    konflikt: int | None   # Index der verletzten Klausel oder None
    schritte: list         # [(Literal, Index der auslösenden Klausel)] in der Reihenfolge des Schlusses


class Propagator:
    """Einheitspropagation über Vorkommenslisten (zählerbasiert). Eine Instanz gehört zu einer festen Klauselmenge und kann beliebig oft laufen."""

    def __init__(self, klauseln, n_gesamt: int):
        self.kl = [tuple(c) for c in klauseln]
        self.n = n_gesamt
        self.vorkommen: dict[int, list[int]] = {}
        for i, c in enumerate(self.kl):
            for l in c:
                self.vorkommen.setdefault(l, []).append(i)

    def lauf(self, feste: dict) -> Prop:
        kl, vork = self.kl, self.vorkommen
        wert: dict[int, bool] = {}
        offen = [len(c) for c in kl]               # Zahl der nicht falschen Literale je Klausel
        erfuellt = [False] * len(kl)
        schritte: list = []
        ursache: dict[int, int | None] = {}        # Variable -> Klausel, die sie erzwungen hat (None: Annahme)
        warte: deque = deque()                     # (Literal, auslösende Klausel oder None für Annahmen)
        for v, b in feste.items():
            warte.append((v if b else -v, None))
        for i, c in enumerate(kl):
            if not c:
                return Prop(wert, i, schritte)
            if len(c) == 1:
                warte.append((c[0], i))
        while warte:
            lit, grund = warte.popleft()
            v = abs(lit)
            if v in wert:
                if wert[v] != (lit > 0):
                    # zwei Schlüsse widersprechen sich: die Klausel, die einen der beiden erzwungen hat, ist verletzt
                    return Prop(wert, grund if grund is not None else ursache[v], schritte)
                continue
            wert[v] = lit > 0
            ursache[v] = grund
            if grund is not None:
                schritte.append((lit, grund))
            for c in vork.get(lit, ()):
                erfuellt[c] = True
            for c in vork.get(-lit, ()):
                offen[c] -= 1
                if erfuellt[c]:
                    continue
                if offen[c] == 0:
                    return Prop(wert, c, schritte)
                if offen[c] == 1:
                    u = next(l for l in kl[c] if abs(l) not in wert)
                    warte.append((u, c))
        return Prop(wert, None, schritte)


def propagiere(klauseln, n_gesamt: int, feste: dict) -> Prop:
    """Einheitspropagation: `feste` ist {Variable: bool}. Ergebnis: Belegung, verletzte Klausel (oder None), Schlüsse mit auslösender Klausel."""
    return Propagator(klauseln, n_gesamt).lauf(feste)


def klauselzustand(klausel, belegung: dict) -> str:
    """„erfüllt“, „verletzt“, „Einheit“ (genau ein offenes Literal, Rest falsch) oder „offen“."""
    offen = 0
    for l in klausel:
        w = belegung.get(abs(l))
        if w is None:
            offen += 1
        elif w == (l > 0):
            return "erfüllt"
    return "verletzt" if offen == 0 else "Einheit" if offen == 1 else "offen"


# ----------------------------------------------------------------------------------------------------------------------- Semantikprüfung


def erfuellbar(klauseln, n_gesamt: int, feste: dict) -> bool:
    """Kleiner Rückwärtssuch-Löser (Einheitspropagation, Verzweigung auf die kleinste offene Variable), unabhängig von `kkd_cdcl`."""
    prop = Propagator(klauseln, n_gesamt)

    def rek(f: dict) -> bool:
        p = prop.lauf(f)
        if p.konflikt is not None:
            return False
        for v in range(1, n_gesamt + 1):
            if v not in p.belegung:
                return rek({**p.belegung, v: True}) or rek({**p.belegung, v: False})
        return True

    return rek(dict(feste))


def semantik_pruefen(verfahren: str, n: int, k: int) -> tuple[int, int]:
    """Für alle 2^n Eingaben: hat die Kodierung eine Fortsetzung auf die Hilfsvariablen genau dann, wenn höchstens k Eingänge wahr sind?
    Gibt (geprüfte Eingaben, Abweichungen) zurück."""
    kod = kodierung(n, k, verfahren)
    abweichungen = 0
    for bits in itertools.product((False, True), repeat=n):
        feste = {i + 1: b for i, b in enumerate(bits)}
        if erfuellbar(kod.klauseln, kod.n_gesamt, feste) != (sum(bits) <= k):
            abweichungen += 1
    return 2 ** n, abweichungen


# ------------------------------------------------------------------------------------------------------------ Vollständigkeit der Propagation


def alle_teilbelegungen(n: int):
    """Alle 3^n Teilbelegungen der Eingänge: None (offen), False, True."""
    return itertools.product((None, False, True), repeat=n)


def zufalls_teilbelegungen(n: int, anzahl: int, seed: int) -> list:
    """`anzahl` Teilbelegungen, jeder Eingang gleichverteilt offen / falsch / wahr (SplitMix64)."""
    rng = SplitMix64(seed)
    return [tuple((None, False, True)[rng.below(3)] for _ in range(n)) for _ in range(anzahl)]


class Vollstaendigkeit(NamedTuple):
    teilbelegungen: int
    verletzungen: int              # Teilbelegungen mit mehr als k wahren Eingängen (die Regel ist verletzt)
    verletzung_erkannt: int        # davon mit Konflikt der Einheitspropagation
    erzwungen: int                 # erzwungene Eingänge (offene Eingänge, die in jeder Fortsetzung falsch sein müssen), summiert
    erzwungen_erkannt: int         # davon von der Einheitspropagation auf falsch gesetzt
    mit_luecke: int                # Teilbelegungen mit mindestens einem übersehenen Schluss oder einer übersehenen Verletzung
    falsch_geschlossen: int        # Konflikt ohne Verletzung oder ein Eingang auf den falschen Wert (Soundness; soll 0 sein)


def erwartung(belegung, k: int) -> tuple[bool, set]:
    """Was die Regel „höchstens k“ aus einer Teilbelegung folgert (geschlossene Form, in den Tests gegen Aufzählung geprüft):
    mehr als k wahre Eingänge verletzen sie; genau k wahre erzwingen alle offenen auf falsch; sonst ist nichts erzwungen."""
    wahr = sum(1 for b in belegung if b is True)
    if wahr > k:
        return True, set()
    if wahr == k:
        return False, {i + 1 for i, b in enumerate(belegung) if b is None}
    return False, set()


def vollstaendigkeit(verfahren: str, n: int, k: int, belegungen) -> Vollstaendigkeit:
    kod = kodierung(n, k, verfahren)
    prop = Propagator(kod.klauseln, kod.n_gesamt)
    zaehl = dict(t=0, v=0, ve=0, e=0, ee=0, luecke=0, falsch=0)
    for bel in belegungen:
        zaehl["t"] += 1
        verletzt, erzwungen = erwartung(bel, k)
        p = prop.lauf({i + 1: b for i, b in enumerate(bel) if b is not None})
        konflikt = p.konflikt is not None
        luecke = False
        if verletzt:
            zaehl["v"] += 1
            zaehl["ve"] += konflikt
            luecke = not konflikt
        else:
            if konflikt:
                zaehl["falsch"] += 1
            else:
                eing = {v for v in range(1, n + 1) if v in p.belegung and bel[v - 1] is None}
                zaehl["e"] += len(erzwungen)
                gefunden = {v for v in eing if p.belegung[v] is False}
                zaehl["ee"] += len(gefunden & erzwungen)
                zaehl["falsch"] += len(eing - erzwungen) > 0
                luecke = bool(erzwungen - gefunden)
        zaehl["luecke"] += luecke
    return Vollstaendigkeit(zaehl["t"], zaehl["v"], zaehl["ve"], zaehl["e"], zaehl["ee"], zaehl["luecke"], zaehl["falsch"])


# ------------------------------------------------------------------------------------------------------------------------ Kontrollpunkte


def graph(n: int, grad: float, seed: int) -> list:
    """Konfliktgraph wie `flat_graph` der Linie: n Aufträge, gerundet n·Grad/2 Kanten (a, b) mit a < b, 0-basiert, deterministisch aus dem Seed."""
    return I.zufallskanten(n, int(round(n * grad / 2)), seed)


class Kontrolle(NamedTuple):
    n: int
    kanten: list
    k: int
    verfahren: str
    klauseln: list
    n_gesamt: int
    n_kanten: int          # die ersten n_kanten Klauseln sind Kantenklauseln, der Rest der Zähler
    kod: Kodierung


def kontrollpunkte(n: int, kanten, k: int, verfahren: str) -> Kontrolle:
    """Vertex Cover höchstens k: jede Unverträglichkeit (a, b) wird an a oder b kontrolliert (Klausel x_a ∨ x_b), höchstens k Kontrollpunkte (Zähler)."""
    kod = kodierung(n, k, verfahren)
    kanten_kl = [(a + 1, b + 1) for a, b in kanten]
    return Kontrolle(n, list(kanten), k, verfahren, kanten_kl + list(kod.klauseln), kod.n_gesamt, len(kanten_kl), kod)


def ist_ueberdeckung(kanten, gewaehlt) -> bool:
    gewaehlt = set(gewaehlt)
    return all(a in gewaehlt or b in gewaehlt for a, b in kanten)


def optimum_aufzaehlung(n: int, kanten) -> int:
    """Kleinstes Vertex Cover durch Aufzählung aller Mengen aufsteigender Größe (nur für kleine n)."""
    for k in range(n + 1):
        for menge in itertools.combinations(range(n), k):
            if ist_ueberdeckung(kanten, menge):
                return k
    return n


_OPTIMA: dict | None = None


def lade_optima() -> dict:
    global _OPTIMA
    if _OPTIMA is None:
        pfad = HIER / C.OPTIMA_DATEI
        _OPTIMA = json.loads(pfad.read_text(encoding="utf-8")) if pfad.exists() else {}
    return _OPTIMA


def optimum(n: int, grad: float, seed: int) -> int:
    """Eingefrorenes Optimum des Konfliktgraphen (n, Grad, Seed) aus `kkd_optima.json` (Messskript tools/optima.py, Gegenprobe OR-Tools CP-SAT)."""
    daten = lade_optima()
    try:
        return int(daten["optima"][f"{n}|{grad}"][C.GRAPH_SEEDS.index(seed)])
    except (KeyError, ValueError, IndexError):
        raise KeyError(f"kein eingefrorenes Optimum für n = {n}, Grad {grad}, Seed {seed}") from None


# ------------------------------------------------------------------------------------------------------------------------------- Löserlauf


def messe_lauf(n: int, kanten, k: int, verfahren: str, budget: int) -> dict:
    """Ein Lauf des CDCL-Lösers auf „Kontrollpunkte höchstens k“. Antwort None heißt: Budget erreicht (nie als unerfüllbar lesen)."""
    f = kontrollpunkte(n, kanten, k, verfahren)
    res = solve(f.n_gesamt, f.klauseln, conflict_budget=budget)
    modell_ok = None
    if res.antwort is True:
        gewaehlt = [v - 1 for v in range(1, n + 1) if res.modell[v]]
        modell_ok = I.pruefe_modell(f.klauseln, res.modell) and len(gewaehlt) <= k and ist_ueberdeckung(kanten, gewaehlt)
    return {"klauseln": len(f.klauseln), "hilfs": f.n_gesamt - n, "konflikte": res.stat["konflikte"], "antwort": res.antwort, "modell_ok": modell_ok}
