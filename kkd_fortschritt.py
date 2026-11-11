"""Live-Messreihe mit Fortschrittsanzeige und Zwischenspeicher (nur Bedienung, keine Rechnung).

Aufgabe ist hier ein Lauf des Lösers (ein Graph, eine Kodierung): `lauf` ruft `kkd_algorithm.messe_lauf` auf und wird je Lauf zwischengespeichert
(`st.cache_data`, höchstens 120 Einträge: vier Einstellungen zu zehn Graphen und drei Kodierungen). `kkd_evaluation.messe_zelle` nimmt die zwischengespeicherte
Fassung als `messe_lauf` entgegen; sonst läuft dort derselbe Code wie ohne Zwischenspeicher. Ändert jemand nur das Konfliktbudget zurück oder startet mit
derselben Einstellung erneut, kommen die schon gerechneten Läufe aus dem Speicher. Der Fortschrittsbalken zählt die fertigen Läufe (die nicht gebaute
binomiale Kodierung zählt nicht mit). Das Ergebnis ist gleich dem von `messe_zelle` ohne Zwischenspeicher (`tests/test_fortschritt.py`)."""

from contextlib import contextmanager

import streamlit as st

import kkd_algorithm as A
import kkd_constants as C
import kkd_evaluation as E

_ZAEHLER = {"gerechnet": 0}


def gerechnet() -> int:
    """Wie viele Läufe in diesem Prozess tatsächlich gerechnet (nicht aus dem Zwischenspeicher geholt) wurden; dient dem Test."""
    return _ZAEHLER["gerechnet"]


@st.cache_data(show_spinner=False, max_entries=120)
def lauf(n: int, kanten: tuple, k: int, verfahren: str, budget: int) -> dict:
    """Ein Lauf, gleich `A.messe_lauf(n, kanten, k, verfahren, budget)`."""
    _ZAEHLER["gerechnet"] += 1
    return A.messe_lauf(n, kanten, k, verfahren, budget)


def _lauf_mit_tupeln(n, kanten, k, verfahren, budget):
    """Die Kanten kommen als Liste; als Tupel von Paaren sind sie ein stabiler Schlüssel für den Zwischenspeicher."""
    return lauf(n, tuple(tuple(e) for e in kanten), k, verfahren, budget)


def anzahl_laeufe(n: int, grad: float, modus: str, k_fest, verfahren, seeds=C.GRAPH_SEEDS) -> int:
    """Wie viele Läufe `messe_zelle` rechnet: je Graph und Kodierung einer, außer die binomiale Kodierung ist zu groß und wird nicht gebaut."""
    ks = E.k_je_graph(n, grad, modus, k_fest, seeds)
    return sum(1 for v in verfahren for k in ks if not (v == "binomial" and A.klauselzahl(v, n, k) > C.BINOMIAL_GRENZE))


def zelle(n: int, grad: float, modus: str, k_fest, verfahren, budget: int, melde=None) -> dict:
    """Die Zelle wie `E.messe_zelle(n, grad, modus, k_fest, verfahren, budget)`; `melde(fertig, gesamt)` wird nach jedem Lauf aufgerufen."""
    gesamt, fertig = anzahl_laeufe(n, grad, modus, k_fest, verfahren), [0]

    def fortschritt(_v, _s):
        fertig[0] += 1
        if melde:
            melde(fertig[0], gesamt)

    return E.messe_zelle(n, grad, modus, k_fest, verfahren, budget, fortschritt=fortschritt, messe_lauf=_lauf_mit_tupeln)


@contextmanager
def fortschrittsbalken(text: str):
    """Fortschrittsbalken mit Beschriftung; liefert `melde(fertig, gesamt)` und räumt den Balken am Ende weg."""
    balken = st.progress(0.0, text=text)

    def melde(fertig: int, gesamt: int) -> None:
        balken.progress(fertig / gesamt, text=f"{text}: {fertig} von {gesamt}")

    try:
        yield melde
    finally:
        balken.empty()
