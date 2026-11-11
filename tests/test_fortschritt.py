"""Live-Messreihe mit Fortschrittsanzeige und Zwischenspeicher: das Ergebnis ist gleich dem ungepufferten, ein anderer Parameter kommt nicht aus dem Speicher."""

import os

from streamlit.testing.v1 import AppTest

import kkd_algorithm as A
import kkd_constants as C
import kkd_evaluation as E
import kkd_fortschritt as F

APP_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app.py")
TIMEOUT = int(os.environ.get("APPTEST_TIMEOUT", "300"))

ZELLEN = ((25, 3.0, "Optimum", None), (25, 3.5, "Optimum − 1", None), (25, 3.0, "fester Wert k", 8), (30, 3.0, "fester Wert k", 12))


def test_zwischengespeicherte_zelle_ist_gleich_der_ungepufferten():
    F.lauf.clear()
    for n, grad, modus, k in ZELLEN:
        direkt = E.messe_zelle(n, grad, modus, k, C.VERFAHREN, 20_000)
        for _ in range(2):                                                   # zweiter Aufruf aus dem Zwischenspeicher
            assert F.zelle(n, grad, modus, k, C.VERFAHREN, 20_000) == direkt, (n, grad, modus, k)


def test_kante_als_liste_oder_tupel_gibt_dieselbe_messung():
    kanten = A.graph(25, 3.0, C.GRAPH_SEEDS[0])
    k = A.optimum(25, 3.0, C.GRAPH_SEEDS[0])
    F.lauf.clear()
    assert F._lauf_mit_tupeln(25, kanten, k, "sinz", 20_000) == A.messe_lauf(25, kanten, k, "sinz", 20_000)
    assert F._lauf_mit_tupeln(25, [list(e) for e in kanten], k, "sinz", 20_000) == A.messe_lauf(25, kanten, k, "sinz", 20_000)


def test_zweiter_aufruf_rechnet_nichts_neu_ein_anderer_parameter_schon():
    F.lauf.clear()
    v0 = F.gerechnet()
    erste = F.zelle(25, 3.0, "Optimum", None, C.VERFAHREN, 20_000)
    gesamt = F.anzahl_laeufe(25, 3.0, "Optimum", None, C.VERFAHREN)
    assert F.gerechnet() - v0 == gesamt and 20 <= gesamt <= 30
    v1 = F.gerechnet()
    assert F.zelle(25, 3.0, "Optimum", None, C.VERFAHREN, 20_000) == erste and F.gerechnet() == v1
    for args, budget in (((25, 3.5, "Optimum", None), 20_000), ((25, 3.0, "Optimum − 1", None), 20_000), ((30, 3.0, "Optimum", None), 20_000), ((25, 3.0, "Optimum", None), 50_000)):
        v = F.gerechnet()
        neu = F.zelle(*args, C.VERFAHREN, budget)
        assert F.gerechnet() - v == F.anzahl_laeufe(*args, C.VERFAHREN), (args, budget)
        assert neu == E.messe_zelle(*args, C.VERFAHREN, budget), (args, budget)
    v = F.gerechnet()
    F.zelle(25, 3.0, "fester Wert k", 6, C.VERFAHREN, 20_000)
    F.zelle(25, 3.0, "fester Wert k", 7, C.VERFAHREN, 20_000)
    zusammen = F.anzahl_laeufe(25, 3.0, "fester Wert k", 6, C.VERFAHREN) + F.anzahl_laeufe(25, 3.0, "fester Wert k", 7, C.VERFAHREN)
    assert F.gerechnet() - v == zusammen, "ein anderes k darf nicht aus dem Zwischenspeicher kommen"


def test_fortschritt_zaehlt_nur_gerechnete_laeufe_und_nennt_die_gesamtzahl():
    F.lauf.clear()
    meldungen = []
    F.zelle(25, 3.0, "Optimum", None, C.VERFAHREN, 20_000, lambda fertig, gesamt: meldungen.append((fertig, gesamt)))
    gesamt = F.anzahl_laeufe(25, 3.0, "Optimum", None, C.VERFAHREN)
    assert meldungen == [(i, gesamt) for i in range(1, gesamt + 1)]
    # die binomiale Kodierung ist bei diesen Größen zu groß und wird nicht gebaut; sie zählt nicht mit (n = 25: 20 von 30 Läufen)
    assert gesamt == 20 and F.anzahl_laeufe(25, 3.0, "Optimum", None, ("sinz", "totalizer")) == 20
    assert F.anzahl_laeufe(60, 3.0, "fester Wert k", 22, C.VERFAHREN) == 20
    assert F.anzahl_laeufe(10, 3.0, "fester Wert k", 2, C.VERFAHREN) == 30


def test_app_zweiter_start_kommt_aus_dem_zwischenspeicher_und_zeigt_dasselbe():
    F.lauf.clear()
    v0 = F.gerechnet()
    at = AppTest.from_file(APP_PATH)
    at.run(timeout=TIMEOUT)
    at.button(key="live_go").click().run(timeout=TIMEOUT)
    assert not at.exception, [str(e) for e in at.exception]
    erste = [d.value.to_dict("records") for d in at.dataframe]
    assert F.gerechnet() - v0 == F.anzahl_laeufe(at.select_slider(key="e3_n").value, at.radio(key="e3_grad").value, at.radio(key="e3_modus").value, None, C.VERFAHREN)
    v = F.gerechnet()
    at.button(key="live_go").click().run(timeout=TIMEOUT)
    assert not at.exception and F.gerechnet() == v
    assert [d.value.to_dict("records") for d in at.dataframe] == erste
