"""Messreihen, Kennzahlen und Verdikte. Jedes Verdikt ist eine reine Funktion (Art, Text); jede Zahl im Text stammt aus den übergebenen Kennzahlen."""

import json
import statistics
from typing import NamedTuple

import kkd_algorithm as A
import kkd_constants as C

# ------------------------------------------------------------------------------------------------------------------------------ Formatierung


def zahl(x, stellen: int = 0) -> str:
    """Deutsche Zahlenschreibweise: Tausenderpunkt, Dezimalkomma. Ganzzahlige Werte ohne Nachkommastellen, wenn `stellen` = 0."""
    if x is None:
        return "–"
    if stellen == 0 and float(x) != int(x):
        stellen = 1 if abs(x * 2 - round(x * 2)) < 1e-9 else 2
    text = f"{x:,.{stellen}f}"
    return text.replace(",", "§").replace(".", ",").replace("§", ".")


def zahl_gross(x) -> str:
    """Wie `zahl`, ab 10 Millionen als Zehnerpotenz („2,3 · 10^16“): so große Klauselzahlen der nicht gebauten binomialen Kodierung sind nur Formelwerte."""
    if x is None or x < 10 ** 7:
        return zahl(x)
    e = len(str(int(x))) - 1
    return f"{x / 10 ** e:.1f}".replace(".", ",") + f" · 10^{e}"


def faktor(x: float) -> str:
    """Verhältnis: ab 10 ganzzahlig, darunter eine Nachkommastelle."""
    return zahl(round(x), 0) if x >= 10 else zahl(round(x, 1), 1)


# ----------------------------------------------------------------------------------------------------------------------------- Messreihe


def zellen_schluessel(n: int, grad: float, modus: str, k_fest: int | None) -> str:
    kurz = {"Optimum": "opt", "Optimum − 1": "opt-1"}.get(modus, f"k{k_fest}")
    return f"{n}|{grad}|{kurz}"


def k_je_graph(n: int, grad: float, modus: str, k_fest: int | None, seeds=C.GRAPH_SEEDS) -> list:
    """Das k jedes Graphen: Optimum, Optimum − 1 oder der feste Wert (das Optimum kommt aus `kkd_optima.json`)."""
    if modus == "fester Wert k":
        return [int(k_fest)] * len(seeds)
    return [A.optimum(n, grad, s) - (1 if modus == "Optimum − 1" else 0) for s in seeds]


def messe_zelle(n: int, grad: float, modus: str, k_fest: int | None, verfahren, budget: int, seeds=C.GRAPH_SEEDS, fortschritt=None) -> dict:
    """Ein Lauf je Graph und Kodierung. Die binomiale Kodierung wird über `BINOMIAL_GRENZE` Klauseln nicht gebaut (nur die Formel steht in der Zelle).
    Erwartung je Graph: erfüllbar genau dann, wenn k >= Optimum."""
    ks = k_je_graph(n, grad, modus, k_fest, seeds)
    opts = [A.optimum(n, grad, s) for s in seeds]
    zelle = {"n": n, "grad": grad, "modus": modus, "k_fest": k_fest, "budget": budget, "seeds": list(seeds), "k": ks, "opt": opts,
             "erwartet": [k >= o for k, o in zip(ks, opts)], "verfahren": {}}
    for v in verfahren:
        je = {"konflikte": [], "antwort": [], "klauseln": [], "hilfs": [], "modell_ok": [], "gebaut": True}
        for s, k in zip(seeds, ks):
            kanten = A.graph(n, grad, s)
            nk = len(kanten) + A.klauselzahl(v, n, k)
            if v == "binomial" and A.klauselzahl(v, n, k) > C.BINOMIAL_GRENZE:
                je["gebaut"] = False
                je["konflikte"].append(None)
                je["antwort"].append(None)
                je["klauseln"].append(nk)
                je["hilfs"].append(0)
                je["modell_ok"].append(None)
                continue
            r = A.messe_lauf(n, kanten, k, v, budget)
            for feld, wert in (("konflikte", r["konflikte"]), ("antwort", r["antwort"]), ("klauseln", r["klauseln"]), ("hilfs", r["hilfs"]),
                               ("modell_ok", r["modell_ok"])):
                je[feld].append(wert)
            if fortschritt:
                fortschritt(v, s)
        zelle["verfahren"][v] = je
    return zelle


def lade_messungen() -> dict:
    pfad = A.HIER / C.MESSUNGEN_DATEI
    return json.loads(pfad.read_text(encoding="utf-8")) if pfad.exists() else {}


def referenz_zelle(n: int, grad: float, modus: str, k_fest: int | None):
    return lade_messungen().get("zellen", {}).get(zellen_schluessel(n, grad, modus, k_fest))


class Kennzahlen(NamedTuple):
    laeufe: int
    median: float | None
    minimum: int | None
    maximum: int | None
    abbrueche: int             # Läufe, die das Konfliktbudget erreicht haben (zählen mit dem Budget)
    falsche_antworten: int     # Antworten (ohne Abbruch), die der Erwartung widersprechen
    klauseln: float | None     # Median der Klauselzahl
    hilfs: float | None        # Median der Hilfsvariablen
    gebaut: bool


def kennzahlen(zelle: dict, v: str) -> Kennzahlen:
    je = zelle["verfahren"][v]
    kl, hv = statistics.median(je["klauseln"]), statistics.median(je["hilfs"])
    if not je["gebaut"]:
        return Kennzahlen(len(je["klauseln"]), None, None, None, 0, 0, kl, hv, False)
    budget = zelle["budget"]
    werte = [budget if a is None else c for c, a in zip(je["konflikte"], je["antwort"])]
    falsch = sum(1 for a, e in zip(je["antwort"], zelle["erwartet"]) if a is not None and a != e)
    falsch += sum(1 for m in je["modell_ok"] if m is False)
    return Kennzahlen(len(werte), statistics.median(werte), min(werte), max(werte), sum(1 for a in je["antwort"] if a is None), falsch, kl, hv, True)


def vergleich_je_graph(zelle: dict, a: str, b: str) -> tuple[int, int, int]:
    """(Graphen mit weniger Konflikten bei `b` als bei `a`, gleich viele, mehr). Abbrüche zählen mit dem Budget."""
    budget = zelle["budget"]

    def konf(v):
        je = zelle["verfahren"][v]
        return [budget if x is None else c for c, x in zip(je["konflikte"], je["antwort"])]

    weniger = gleich = mehr = 0
    for ca, cb in zip(konf(a), konf(b)):
        weniger += cb < ca
        gleich += cb == ca
        mehr += cb > ca
    return weniger, gleich, mehr


# ----------------------------------------------------------------------------------------------------------------------------------- Verdikte


def verdict_groesse(n: int, k: int, klauseln: dict, hilfs: dict) -> tuple[str, str]:
    """Experiment 2: Größenverhältnis am gewählten Punkt (n, k). `klauseln` und `hilfs` je Kodierung (Formelwerte)."""
    b, s, t = klauseln["binomial"], klauseln["sinz"], klauseln["totalizer"]
    if k >= n:
        return "info", f"Bei n = {n}, k = {k} ist die Regel nie verletzt (k ≥ n): keine Kodierung braucht eine Klausel."
    text = (f"Bei n = {n}, k = {k} hat die binomiale Kodierung {zahl(b)} Klauseln, der Sinz-Zähler {zahl(s)} ({zahl(hilfs['sinz'])} Hilfsvariablen), "
            f"der Totalizer {zahl(t)} ({zahl(hilfs['totalizer'])} Hilfsvariablen).")
    if s > 0:
        ist = "ist hier nur" if b < s else "ist"
        text += f" Die binomiale Kodierung {ist} {faktor(b / s)}-mal so groß wie der Sinz-Zähler"
        text += f" und {faktor(b / t)}-mal so groß wie der Totalizer." if t > 0 else "."
    kind = "success" if b > 10 * s else "info"
    return kind, text


def _modus_text(zelle: dict) -> str:
    modus, ks = zelle["modus"], zelle["k"]
    if modus == "Optimum":
        return "Am Optimum (erfüllbar)"
    if modus == "Optimum − 1":
        return "Bei k = Optimum − 1 (unerfüllbar)"
    erwartet = zelle["erwartet"]
    zustand = "unerfüllbar" if not any(erwartet) else "erfüllbar" if all(erwartet) else f"in {sum(erwartet)} von {len(erwartet)} Graphen erfüllbar"
    return f"Bei k = {ks[0]} ({zustand})"


def verdict_konflikte(zelle: dict) -> tuple[str, str]:
    """Experiment 3: Median der Konflikte, Sinz-Zähler gegen Totalizer, mit der Zählung über die Graphen (Schwelle `SCHWELLE_KAUM`)."""
    vs = zelle["verfahren"]
    if "sinz" not in vs or "totalizer" not in vs:
        return "info", "Für den Vergleich fehlen Sinz-Zähler oder Totalizer in dieser Messreihe."
    s, t = kennzahlen(zelle, "sinz"), kennzahlen(zelle, "totalizer")
    n_graphen = s.laeufe
    kopf = f"{_modus_text(zelle)}, n = {zelle['n']}, {n_graphen} Graphen"
    abbruch = ""
    if s.abbrueche or t.abbrueche:
        abbruch = (f" Abbrüche am Budget ({zahl(zelle['budget'])} Konflikte): Sinz {s.abbrueche}, Totalizer {t.abbrueche}; sie zählen mit dem Budget, "
                   "die Mediane sind dann untere Schranken.")
    falsch = ""
    if s.falsche_antworten or t.falsche_antworten:
        falsch = f" **Achtung:** {s.falsche_antworten + t.falsche_antworten} Antworten widersprechen der Erwartung."
    if not s.median or not t.median:
        return "warning", f"{kopf}: Der Median der Konflikte ist 0, ein Verhältnis ist nicht definiert (Sinz {zahl(s.median)}, Totalizer {zahl(t.median)})." + abbruch + falsch
    weniger, gleich, mehr = vergleich_je_graph(zelle, "sinz", "totalizer")
    zaehlung = f"in {weniger} von {n_graphen} Graphen hat der Totalizer weniger Konflikte, in {gleich} gleich viele, in {mehr} mehr"
    r = s.median / t.median
    werte = f"Sinz-Zähler {zahl(s.median)} (Maximum {zahl(s.maximum)}), Totalizer {zahl(t.median)} (Maximum {zahl(t.maximum)})"
    schwach = " Die Zählung stützt die Richtung im Median nur schwach: der Median-Faktor hängt stark von wenigen Graphen mit langer Suche ab."
    if r >= C.SCHWELLE_KAUM:
        text = f"{kopf}: Der Sinz-Zähler braucht im Median das {faktor(r)}-Fache der Konflikte des Totalizers ({werte}); {zaehlung}."
        text += schwach if weniger < 0.7 * n_graphen else ""
        kind = "success"
    elif t.median / s.median >= C.SCHWELLE_KAUM:
        text = f"{kopf}: Der Totalizer braucht im Median das {faktor(t.median / s.median)}-Fache der Konflikte des Sinz-Zählers ({werte}); {zaehlung}."
        text += schwach if mehr < 0.7 * n_graphen else ""
        kind = "success"
    else:
        text = f"{kopf}: kaum Unterschied im Median (Verhältnis Sinz-Zähler zu Totalizer {faktor(r)}; {werte}); {zaehlung}."
        kind = "info"
    if "binomial" in vs:
        b = kennzahlen(zelle, "binomial")
        if b.gebaut:
            text += f" Binomial: Median {zahl(b.median)} Konflikte bei {zahl(b.klauseln)} Klauseln (Sinz-Zähler {zahl(s.klauseln)})."
        else:
            text += f" Binomial nicht gebaut: {zahl_gross(b.klauseln)} Klauseln liegen über der Grenze von {zahl(C.BINOMIAL_GRENZE)}."
    return kind, text + abbruch + falsch


def verdict_vollstaendigkeit(ergebnisse: dict, n: int, k: int) -> tuple[str, str]:
    """Experiment 4: `ergebnisse` {Kodierung: Vollstaendigkeit}. Nennt immer die Zahl der geprüften Teilbelegungen."""
    teil = next(iter(ergebnisse.values())).teilbelegungen
    luecken = {v: r.mit_luecke for v, r in ergebnisse.items()}
    falsch = sum(r.falsch_geschlossen for r in ergebnisse.values())
    erz = next(iter(ergebnisse.values())).erzwungen
    verl = next(iter(ergebnisse.values())).verletzungen
    basis = (f"Bei n = {n}, k = {k} wurden {zahl(teil)} Teilbelegungen geprüft ({zahl(verl)} verletzen die Regel, in den übrigen sind insgesamt "
             f"{zahl(erz)} Eingänge erzwungen).")
    if falsch:
        return "error", basis + f" **Achtung:** {falsch} Schlüsse der Einheitspropagation widersprechen der Regel."
    if not any(luecken.values()):
        return "success", basis + " Bei allen drei Kodierungen bleibt keine erzwungene Belegung und keine Verletzung übersehen: die Einheitspropagation ist hier so stark wie die Regel selbst."
    teile = ", ".join(f"{C.VERFAHREN_LABEL[v]} {luecken[v]}" for v in ergebnisse)
    return "warning", basis + f" Teilbelegungen mit mindestens einem übersehenen Schluss: {teile}."


# ------------------------------------------------------------------------------------------------------------------------------- Wachstum


def gebaute_klauselzahl(verfahren: str, n: int, k: int) -> int | None:
    """Klauseln der gebauten Kodierung (Kern-Kopie); die binomiale Kodierung wird über `BINOMIAL_GRENZE` Klauseln nicht gebaut (None)."""
    if verfahren == "binomial" and A.klauselzahl(verfahren, n, k) > C.BINOMIAL_GRENZE:
        return None
    return len(A.K.hoechstens(list(range(1, n + 1)), k, A.K.Hilfsvariablen(n), verfahren))


def wachstum(achse: str, fest: int) -> dict:
    """Klauseln über n (k = `fest`, `achse` = "n") bzw. über k (n = `fest`, `achse` = "k"): Formelwert und gebauter Wert je Kodierung."""
    xs = list(C.E2_N_PUNKTE if achse == "n" else C.E2_K_PUNKTE)
    klauseln = {v: [] for v in C.VERFAHREN}
    gebaut = {v: [] for v in C.VERFAHREN}
    for x in xs:
        n, k = (x, fest) if achse == "n" else (fest, x)
        for v in C.VERFAHREN:
            klauseln[v].append(A.klauselzahl(v, n, k))
            gebaut[v].append(gebaute_klauselzahl(v, n, k))
    return {"xs": xs, "klauseln": klauseln, "gebaut": gebaut}
