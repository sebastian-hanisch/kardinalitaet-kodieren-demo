"""Claims: jede Zahl der README-Tabelle „Befunde“ (DEMO-PLAYBOOK §4, §11a).

Drei Quellen: (1) exakte Rechnung (Klauselzahlen, Formeln, Handbeispiel, Aufzählung), (2) die vorgerechneten Messreihen `kkd_messungen.json` (Budget 300.000,
10 feste Graphen je Zelle; die erwarteten Werte stehen unten als Tabelle, damit eine stille Änderung der Datei auffällt), (3) Neumessung billiger Zellen gegen die Datei.
Nicht hier stehen die Zahlen der Gegenprobe (`tools/gegenprobe.py`) und die Werte des Plans."""

import math
import statistics

import pytest

import kkd_algorithm as A
import kkd_constants as C
import kkd_evaluation as E

# Zelle -> (Median Sinz, Maximum Sinz, Median Totalizer, Maximum Totalizer, Totalizer weniger, gleich, mehr, Klauseln Sinz, Klauseln Totalizer, Hilfsvariablen Sinz, Hilfsvariablen Totalizer)
# Klauseln einschließlich der Kantenklauseln; Median über die zehn Graphen.
# @@ZELLEN@@
ZELLEN = {
    "25|3.0|opt": (22.5, 62, 30.5, 80, 3, 1, 6, 626.0, 457.0, 288.0, 106.0),
    "25|3.0|opt-1": (65.5, 77, 60.5, 107, 4, 0, 6, 579.0, 444.0, 264.0, 104.0),
    "25|3.5|opt": (38.5, 141, 48.5, 83, 4, 0, 6, 679.0, 463.0, 312.0, 107.0),
    "25|3.5|opt-1": (74.5, 120, 82.0, 117, 5, 0, 5, 632.0, 463.0, 288.0, 106.0),
    "30|3.0|opt": (73.0, 191, 78.0, 152, 5, 0, 5, 872.0, 629.0, 406.0, 133.0),
    "30|3.0|opt-1": (119.0, 293, 129.5, 261, 3, 0, 7, 815.0, 598.0, 377.0, 130.0),
    "30|3.5|opt": (68.0, 267, 51.5, 242, 6, 0, 4, 964.5, 636.0, 449.5, 134.5),
    "30|3.5|opt-1": (194.5, 312, 196.5, 282, 5, 0, 5, 907.5, 636.0, 420.5, 133.5),
    "40|3.0|opt": (148.5, 441, 77.0, 456, 7, 0, 3, 1562.0, 1057.0, 741.0, 196.0),
    "40|3.0|opt-1": (585.5, 1397, 526.0, 1386, 5, 0, 5, 1485.0, 1016.0, 702.0, 193.0),
    "40|3.5|opt": (120.0, 1594, 189.5, 411, 6, 0, 4, 1726.0, 1067.0, 819.0, 198.0),
    "40|3.5|opt-1": (584.0, 1241, 592.5, 1388, 7, 0, 3, 1649.0, 1067.0, 780.0, 197.0),
    "50|3.0|opt": (651.0, 4359, 258.0, 1614, 6, 0, 4, 2500.5, 1587.0, 1200.5, 261.5),
    "50|3.0|opt-1": (1852.5, 4851, 1915.0, 4513, 6, 0, 4, 2403.5, 1561.5, 1151.5, 259.5),
    "50|3.5|opt": (1025.5, 4589, 410.0, 1151, 6, 0, 4, 2659.0, 1600.0, 1274.0, 263.0),
    "50|3.5|opt-1": (1792.0, 4086, 1762.0, 3661, 6, 0, 4, 2562.0, 1600.0, 1225.0, 262.0),
    "60|3.0|opt": (3539.5, 7366, 815.0, 4687, 9, 0, 1, 3542.0, 2217.0, 1711.0, 326.0),
    "60|3.0|opt-1": (8129.5, 14937, 6507.5, 10306, 8, 0, 2, 3425.0, 2156.0, 1652.0, 323.0),
    "60|3.5|opt": (3057.0, 15338, 1373.5, 4545, 7, 0, 3, 3791.0, 2232.0, 1829.0, 328.0),
    "60|3.5|opt-1": (7185.0, 19108, 5944.5, 11813, 7, 0, 3, 3674.0, 2232.0, 1770.0, 327.0),
    "25|3.0|k5": (10.0, 14, 10.0, 11, 4, 3, 3, 297.0, 317.0, 120.0, 85.0),
    "25|3.0|k8": (25.0, 29, 22.5, 33, 8, 0, 2, 438.0, 375.0, 192.0, 95.0),
    "60|3.0|k22": (837.5, 1067, 507.0, 739, 10, 0, 0, 2723.0, 1832.0, 1298.0, 305.0),
    "60|3.0|k26": (3272.0, 4493, 2274.0, 2727, 9, 0, 1, 3191.0, 2040.0, 1534.0, 317.0),
}


@pytest.fixture(scope="module")
def zellen():
    return E.lade_messungen()["zellen"]


def _stat(z):
    s, t = E.kennzahlen(z, "sinz"), E.kennzahlen(z, "totalizer")
    return (s.median, s.maximum, t.median, t.maximum, *E.vergleich_je_graph(z, "sinz", "totalizer"), s.klauseln, t.klauseln, s.hilfs, t.hilfs)


def _verhaeltnis(zellen, key):
    s, t = E.kennzahlen(zellen[key], "sinz"), E.kennzahlen(zellen[key], "totalizer")
    return s.median / t.median


# --- Exakte Rechnung ----------------------------------------------------------------------------------------------------------------------

def test_claim_groesse_n25_k5():
    assert (A.klauselzahl("binomial", 25, 5), A.klauselzahl("sinz", 25, 5), A.hilfsvariablen("sinz", 25, 5)) == (177100, 259, 120)
    assert (A.klauselzahl("totalizer", 25, 5), A.hilfsvariablen("totalizer", 25, 5)) == (279, 85)
    assert round(177100 / 259) == 684 and round(177100 / 279) == 635
    k = A.kontrollpunkte(25, A.graph(25, 3.0, 600), 5, "binomial")                      # mit den 38 Kantenklauseln
    assert (len(k.klauseln), k.n_kanten) == (177138, 38)
    assert (len(A.kontrollpunkte(25, A.graph(25, 3.0, 600), 5, "sinz").klauseln), len(A.kontrollpunkte(25, A.graph(25, 3.0, 600), 5, "totalizer").klauseln)) == (297, 317)


def test_claim_handbeispiel_zahlen():
    assert [(A.klauselzahl(v, 4, 2), A.hilfsvariablen(v, 4, 2)) for v in ("binomial", "sinz", "totalizer")] == [(4, 0), (13, 6), (15, 7)]
    assert [A.semantik_pruefen(v, 4, 2) for v in ("binomial", "sinz", "totalizer")] == [(16, 0)] * 3
    for v, schluesse in (("binomial", 2), ("sinz", 8), ("totalizer", 9)):
        kod = A.kodierung(4, 2, v)
        p = A.propagiere(kod.klauseln, kod.n_gesamt, {1: True, 2: True})
        assert len(p.schritte) == schluesse and (p.belegung[3], p.belegung[4]) == (False, False)


def test_claim_schluesse_bis_zum_konflikt_im_handbeispiel():
    """README („Befunde und Korrekturen“): die Zahl der Schlüsse bis zum Konflikt hängt von der Reihenfolge der Warteschlange ab."""
    zahlen = []
    for v in ("binomial", "sinz", "totalizer"):
        kod = A.kodierung(4, 2, v)
        p = A.propagiere(kod.klauseln, kod.n_gesamt, {1: True, 2: True, 3: True})
        assert p.konflikt is not None
        zahlen.append(len(p.schritte))
    assert zahlen == [0, 5, 4]


def test_claim_vollstaendigkeit():
    for v in ("binomial", "sinz", "totalizer"):
        r4 = A.vollstaendigkeit(v, 4, 2, A.alle_teilbelegungen(4))
        assert (r4.teilbelegungen, r4.verletzungen, r4.erzwungen, r4.mit_luecke, r4.falsch_geschlossen) == (81, 9, 24, 0, 0)
        r6 = A.vollstaendigkeit(v, 6, 2, A.alle_teilbelegungen(6))
        assert (r6.teilbelegungen, r6.verletzungen, r6.verletzung_erkannt, r6.erzwungen, r6.erzwungen_erkannt, r6.mit_luecke, r6.falsch_geschlossen) == (729, 233, 233, 480, 480, 0, 0)
        r10 = A.vollstaendigkeit(v, 10, 3, A.zufalls_teilbelegungen(10, 5000, 35))
        assert (r10.teilbelegungen, r10.verletzungen, r10.verletzung_erkannt, r10.erzwungen, r10.erzwungen_erkannt, r10.mit_luecke, r10.falsch_geschlossen) == (5000, 2155, 2155, 4642, 4642, 0, 0)
    for seed in range(5):                                           # „keine übersehen“ gilt für andere Zufalls-Seeds, die Zahlen 2.155 und 4.642 nicht
        for v in ("binomial", "sinz", "totalizer"):
            r = A.vollstaendigkeit(v, 10, 3, A.zufalls_teilbelegungen(10, 5000, seed))
            assert r.mit_luecke == 0 and r.falsch_geschlossen == 0 and r.verletzung_erkannt == r.verletzungen and r.erzwungen_erkannt == r.erzwungen, (v, seed)


# --- Vorgerechnete Messreihen -----------------------------------------------------------------------------------------------------------------

def test_die_messreihen_haben_die_erwarteten_zellen(zellen):
    assert set(zellen) == set(ZELLEN) == {E.zellen_schluessel(*z) for z in C.REFERENZ_ZELLEN} and len(zellen) == 24
    assert all(z["budget"] == C.BUDGET_REFERENZ == 300000 and len(z["seeds"]) == 10 for z in zellen.values())


@pytest.mark.parametrize("key", list(ZELLEN))
def test_zelle_stimmt_mit_der_tabelle_ueberein(zellen, key):
    assert _stat(zellen[key]) == ZELLEN[key], key


def test_kein_abbruch_und_alle_antworten_stimmen(zellen):
    antworten = 0
    for key, z in zellen.items():
        for v in ("sinz", "totalizer"):
            kz = E.kennzahlen(z, v)
            assert kz.abbrueche == 0 and kz.falsche_antworten == 0, (key, v)
            antworten += kz.laeufe
    assert antworten == 24 * 2 * 10 and E.kennzahlen(zellen["25|3.0|k5"], "binomial").falsche_antworten == 0


def test_claim_klein_und_gleich(zellen):
    z = zellen["25|3.0|k5"]
    kz = {v: E.kennzahlen(z, v) for v in C.VERFAHREN}
    assert [(kz[v].median, kz[v].maximum) for v in C.VERFAHREN] == [(8.5, 10), (10, 14), (10, 11)]
    assert [kz[v].klauseln for v in C.VERFAHREN] == [177138, 297, 317] and [kz[v].hilfs for v in C.VERFAHREN] == [0, 120, 85]
    z8 = zellen["25|3.0|k8"]
    assert E.kennzahlen(z8, "binomial").gebaut is False and E.kennzahlen(z8, "binomial").klauseln == 2043013 == 38 + A.klauselzahl("binomial", 25, 8)
    assert (E.kennzahlen(z8, "sinz").median, E.kennzahlen(z8, "sinz").maximum, E.kennzahlen(z8, "totalizer").median, E.kennzahlen(z8, "totalizer").maximum) == (25, 29, 22.5, 33)


def test_claim_am_optimum(zellen):
    gerundet = {k: round(_verhaeltnis(zellen, k), 1) for k in zellen if k.endswith("|opt")}
    assert [gerundet[f"{n}|{g}|opt"] for n in (25, 30, 40) for g in (3.0, 3.5)] == [0.7, 0.8, 0.9, 1.3, 1.9, 0.6]
    assert [gerundet[f"{n}|{g}|opt"] for n in (50, 60) for g in (3.0, 3.5)] == [2.5, 2.5, 4.3, 2.2]
    # Zählung je Graph (Totalizer weniger / gleich / mehr) und zweiseitiger Vorzeichentest: nur n = 60, Grad 3 ist statistisch sichtbar
    zaehlung = {(n, g): E.vergleich_je_graph(zellen[f"{n}|{g}|opt"], "sinz", "totalizer") for n in (50, 60) for g in (3.0, 3.5)}
    assert zaehlung == {(50, 3.0): (6, 0, 4), (50, 3.5): (6, 0, 4), (60, 3.0): (9, 0, 1), (60, 3.5): (7, 0, 3)}

    def p_zweiseitig(a, b):
        n, k = a + b, min(a, b)
        return min(1.0, 2 * sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n)
    assert [round(p_zweiseitig(w, m), 2) for (w, _, m) in zaehlung.values()] == [0.75, 0.75, 0.02, 0.34]


def test_claim_knapp_unter_dem_optimum(zellen):
    verh = {k: _verhaeltnis(zellen, k) for k in zellen if k.endswith("|opt-1")}
    assert len(verh) == 10 and min(round(v, 1) for v in verh.values()) == 0.9 and max(round(v, 1) for v in verh.values()) == 1.2
    assert all(0.9 <= round(v, 1) <= 1.1 for k, v in verh.items() if not k.startswith("60|"))
    assert [round(verh[f"60|{g}|opt-1"], 1) for g in (3.0, 3.5)] == [1.2, 1.2]
    z = zellen["60|3.0|opt-1"]
    s, t = E.kennzahlen(z, "sinz"), E.kennzahlen(z, "totalizer")
    assert (s.median, s.maximum, t.median, t.maximum) == (8129.5, 14937, 6507.5, 10306)


def test_claim_deutlich_unter_dem_optimum(zellen):
    for key, (ms, xs, mt, xt, verh, weniger) in {"60|3.0|k22": (837.5, 1067, 507, 739, 1.7, 10), "60|3.0|k26": (3272, 4493, 2274, 2727, 1.4, 9)}.items():
        s, t = E.kennzahlen(zellen[key], "sinz"), E.kennzahlen(zellen[key], "totalizer")
        assert (s.median, s.maximum, t.median, t.maximum) == (ms, xs, mt, xt)
        assert round(s.median / t.median, 1) == verh and E.vergleich_je_graph(zellen[key], "sinz", "totalizer")[0] == weniger
        assert zellen[key]["erwartet"] == [False] * 10 and zellen[key]["k"] == [int(key.split("|k")[1])] * 10


def test_claim_groesse_im_graphen(zellen):
    z = {n: (E.kennzahlen(zellen[f"{n}|3.0|opt"], "sinz"), E.kennzahlen(zellen[f"{n}|3.0|opt"], "totalizer")) for n in (25, 40, 60)}
    assert [(z[n][0].hilfs, z[n][1].hilfs) for n in (25, 40, 60)] == [(288, 106), (741, 196), (1711, 326)]
    assert [(z[n][0].klauseln, z[n][1].klauseln) for n in (25, 40, 60)] == [(626, 457), (1562, 1057), (3542, 2217)]


def test_claim_zaehlung_neben_dem_verhaeltnis_n50(zellen):
    z = zellen["50|3.0|opt"]
    assert round(_verhaeltnis(zellen, "50|3.0|opt"), 1) == 2.5 and E.vergleich_je_graph(z, "sinz", "totalizer")[0] == 6


def test_claim_totalizer_median_hoechstens_sinz_median(zellen):
    """README („Befunde und Korrekturen“): in 15 von 24 vorgerechneten Zellen liegt der Totalizer-Median höchstens beim Sinz-Median."""
    assert sum(E.kennzahlen(z, "totalizer").median <= E.kennzahlen(z, "sinz").median for z in zellen.values()) == 15


# --- Neumessung billiger Zellen gegen die Datei ----------------------------------------------------------------------------------------------

@pytest.mark.parametrize("n, grad, modus", [(25, 3.0, "Optimum"), (30, 3.5, "Optimum")])
def test_neumessung_gleicht_der_datei(zellen, n, grad, modus):
    alt = zellen[E.zellen_schluessel(n, grad, modus, None)]
    neu = E.messe_zelle(n, grad, modus, None, ("sinz", "totalizer"), C.BUDGET_REFERENZ)
    assert neu["k"] == alt["k"] and neu["erwartet"] == alt["erwartet"]
    for v in ("sinz", "totalizer"):
        assert neu["verfahren"][v]["klauseln"] == alt["verfahren"][v]["klauseln"] and neu["verfahren"][v]["hilfs"] == alt["verfahren"][v]["hilfs"]
        assert neu["verfahren"][v]["antwort"] == alt["verfahren"][v]["antwort"]
        # Konfliktzahlen: auf jeder Plattform dieselbe Zahl erwartet (ganzzahlige Zufallszahlen); als Band, falls Gleitkommarundung die Verzweigung verschiebt
        assert statistics.median(neu["verfahren"][v]["konflikte"]) == pytest.approx(statistics.median(alt["verfahren"][v]["konflikte"]), rel=0.3, abs=5)


def test_preset_hilfetexte_stimmen_mit_den_verdikten(zellen):
    """Die Hilfetexte der Presets nennen Verhältnisse und Richtungen; hier gegen die vorgerechneten Zellen und die Verdikt-Arten."""
    def verdikt(name):
        p = C.PRESETS[name]
        modus = p["e3_modus"]
        return E.verdict_konflikte(E.referenz_zelle(p["e3_n"], p["e3_grad"], modus, p.get("e3_k") if modus == "fester Wert k" else None))
    kind, text = verdikt("Am Optimum")
    assert kind == "success" and "Der Sinz-Zähler braucht im Median das 1,9-Fache" in text
    kind, text = verdikt("Knapp unter dem Optimum")
    assert kind == "info" and "kaum Unterschied im Median (Verhältnis Sinz-Zähler zu Totalizer 1,1;" in text
    kind, text = verdikt("Deutlich unter dem Optimum")
    assert kind == "success" and "Der Sinz-Zähler braucht im Median das 1,7-Fache" in text
    kind, text = verdikt("Klein und gleich")
    assert kind == "info" and "Binomial: Median 8,5 Konflikte bei 177.138 Klauseln" in text and "Sinz-Zähler 10 (Maximum 14), Totalizer 10 (Maximum 11)" in text
