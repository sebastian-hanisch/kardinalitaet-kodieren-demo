"""Verdikte an von Hand gesetzten Werten (DEMO-PLAYBOOK §12): jede Zahl im Text und jede Schwelle der Art steht hier.

Ein Verdikt ist eine reine Funktion (Art, Text) und bekommt Zeilen, nicht Seeds. Die Zellen unten sind von Hand gebaut: zehn Graphen, Konflikte je Kodierung."""

import kkd_algorithm as A
import kkd_constants as C
import kkd_evaluation as E


def zelle(sinz, tot, modus="Optimum", antwort=None, budget=1000, k=None, erwartet=None, binomial=None, n=40):
    """Zelle mit zehn Graphen. `antwort` ist die Antwort aller Läufe (None = Abbruch), `erwartet` die erwartete Antwort je Graph."""
    anz = len(sinz)
    erwartet = erwartet if erwartet is not None else [modus == "Optimum"] * anz
    ant = antwort if antwort is not None else list(erwartet)
    je = lambda konf, kl, hv: {"konflikte": konf, "antwort": list(ant), "klauseln": [kl] * anz, "hilfs": [hv] * anz, "modell_ok": [None] * anz, "gebaut": True}
    z = {"n": n, "grad": 3.0, "modus": modus, "k_fest": None, "budget": budget, "seeds": list(range(anz)), "k": k or [20] * anz, "opt": [20] * anz,
         "erwartet": erwartet, "verfahren": {"sinz": je(sinz, 1500, 700), "totalizer": je(tot, 1000, 200)}}
    if binomial:
        z["verfahren"]["binomial"] = binomial
    return z


# --- Experiment 2 -------------------------------------------------------------------------------------------------------------------------

def test_verdict_groesse_nennt_alle_zahlen_und_verhaeltnisse():
    kl = {"binomial": 177100, "sinz": 259, "totalizer": 279}
    hv = {"binomial": 0, "sinz": 120, "totalizer": 85}
    kind, text = E.verdict_groesse(25, 5, kl, hv)
    assert kind == "success"
    assert "n = 25, k = 5" in text and "177.100 Klauseln" in text and "259 (120 Hilfsvariablen)" in text and "279 (85 Hilfsvariablen)" in text
    assert "684-mal so groß wie der Sinz-Zähler" in text and "635-mal so groß wie der Totalizer" in text        # 177100 / 259 = 683,8; 177100 / 279 = 634,8


def test_verdict_groesse_schwelle_zehnfach_und_kleiner_als_der_zaehler():
    assert E.verdict_groesse(10, 3, {"binomial": 2590, "sinz": 259, "totalizer": 300}, {"sinz": 1, "totalizer": 1})[0] == "info"      # genau das Zehnfache: nicht mehr
    assert E.verdict_groesse(10, 3, {"binomial": 2591, "sinz": 259, "totalizer": 300}, {"sinz": 1, "totalizer": 1})[0] == "success"
    kind, text = E.verdict_groesse(4, 2, {"binomial": 4, "sinz": 13, "totalizer": 15}, {"sinz": 6, "totalizer": 7})
    assert kind == "info" and "ist hier nur 0,3-mal so groß wie der Sinz-Zähler und 0,3-mal so groß wie der Totalizer" in text


def test_verdict_groesse_k_ab_n():
    kind, text = E.verdict_groesse(4, 4, {"binomial": 0, "sinz": 0, "totalizer": 0}, {"sinz": 0, "totalizer": 0})
    assert kind == "info" and "k ≥ n" in text and "n = 4, k = 4" in text


# --- Experiment 3 -------------------------------------------------------------------------------------------------------------------------

def test_verdict_konflikte_deutlicher_unterschied_mit_zaehlung():
    z = zelle(sinz=[300, 280, 290, 310, 270, 300, 260, 320, 330, 250], tot=[200, 150, 210, 100, 220, 190, 240, 300, 150, 140])
    kind, text = E.verdict_konflikte(z)                      # Mediane 295 und 195: Verhältnis 1,51
    assert kind == "success"
    assert text.startswith("Am Optimum (erfüllbar), n = 40, 10 Graphen: Der Sinz-Zähler braucht im Median das 1,5-Fache der Konflikte des Totalizers")
    assert "Sinz-Zähler 295 (Maximum 330), Totalizer 195 (Maximum 300)" in text
    assert "in 10 von 10 Graphen hat der Totalizer weniger Konflikte, in 0 gleich viele, in 0 mehr" in text


def test_verdict_konflikte_schwelle_1_2_ist_inklusive():
    kind, text = E.verdict_konflikte(zelle(sinz=[60] * 10, tot=[50] * 10))
    assert kind == "success" and "das 1,2-Fache" in text                                  # genau 1,2: noch ein Unterschied
    kind, text = E.verdict_konflikte(zelle(sinz=[59] * 10, tot=[50] * 10))                # 1,18
    assert kind == "info" and "kaum Unterschied im Median (Verhältnis Sinz-Zähler zu Totalizer 1,2;" in text
    assert "in 0 von 10 Graphen hat der Totalizer weniger" not in text and "in 10 von 10 Graphen hat der Totalizer weniger" in text


def test_verdict_konflikte_umgekehrte_richtung_und_gemischte_zaehlung():
    kind, text = E.verdict_konflikte(zelle(sinz=[50] * 10, tot=[60] * 10))
    assert kind == "success" and "Der Totalizer braucht im Median das 1,2-Fache der Konflikte des Sinz-Zählers" in text
    assert "in 0 von 10 Graphen hat der Totalizer weniger Konflikte, in 0 gleich viele, in 10 mehr" in text
    kind, text = E.verdict_konflikte(zelle(sinz=[10, 20, 30, 40, 50, 60, 70, 80, 90, 100], tot=[10, 20, 30, 40, 50, 60, 70, 80, 95, 90]))
    assert kind == "info" and "in 1 von 10 Graphen hat der Totalizer weniger Konflikte, in 8 gleich viele, in 1 mehr" in text


def test_verdict_konflikte_modustexte():
    gleich = dict(sinz=[100] * 10, tot=[100] * 10)
    assert E.verdict_konflikte(zelle(modus="Optimum − 1", **gleich))[1].startswith("Bei k = Optimum − 1 (unerfüllbar), n = 40, 10 Graphen:")
    z = zelle(modus="fester Wert k", k=[22] * 10, erwartet=[False] * 10, **gleich)
    assert E.verdict_konflikte(z)[1].startswith("Bei k = 22 (unerfüllbar), n = 40, 10 Graphen:")
    z = zelle(modus="fester Wert k", k=[20] * 10, erwartet=[True] * 3 + [False] * 7, antwort=[True] * 3 + [False] * 7, **gleich)
    assert E.verdict_konflikte(z)[1].startswith("Bei k = 20 (in 3 von 10 Graphen erfüllbar), n = 40")


def test_verdict_konflikte_abbrueche_zaehlen_mit_dem_budget_und_werden_genannt():
    sinz = [1000] * 8 + [400, 500]
    z = zelle(sinz=sinz, tot=[100] * 10, modus="Optimum − 1", budget=1000, antwort=[None] * 8 + [False, False], erwartet=[False] * 10)
    z["verfahren"]["totalizer"]["antwort"] = [False] * 10                                 # der Totalizer bricht nie ab
    kind, text = E.verdict_konflikte(z)
    assert "Sinz-Zähler 1.000 (Maximum 1.000)" in text and "Abbrüche am Budget (1.000 Konflikte): Sinz 8, Totalizer 0" in text and "untere Schranken" in text
    assert "das 10,0-Fache" not in text and "das 10-Fache" in text                      # Median 1000 gegen 100: ab 10 ganzzahlig


def test_verdict_konflikte_nennt_falsche_antworten_und_median_null():
    z = zelle(sinz=[100] * 10, tot=[100] * 10, antwort=[False] * 10)                     # erwartet erfüllbar, geantwortet unerfüllbar: 20 falsche Antworten
    assert "**Achtung:** 20 Antworten widersprechen der Erwartung." in E.verdict_konflikte(z)[1]
    kind, text = E.verdict_konflikte(zelle(sinz=[0] * 10, tot=[0] * 10))
    assert kind == "warning" and "Median der Konflikte ist 0" in text


def test_verdict_konflikte_binomial_gebaut_und_nicht_gebaut():
    gebaut = {"konflikte": [9] * 10, "antwort": [False] * 10, "klauseln": [177138] * 10, "hilfs": [0] * 10, "modell_ok": [None] * 10, "gebaut": True}
    z = zelle(sinz=[10] * 10, tot=[10] * 10, modus="fester Wert k", k=[5] * 10, erwartet=[False] * 10, binomial=gebaut)
    assert "Binomial: Median 9 Konflikte bei 177.138 Klauseln (Sinz-Zähler 1.500)." in E.verdict_konflikte(z)[1]
    ungebaut = {"konflikte": [None] * 10, "antwort": [None] * 10, "klauseln": [5000000] * 10, "hilfs": [0] * 10, "modell_ok": [None] * 10, "gebaut": False}
    z = zelle(sinz=[10] * 10, tot=[10] * 10, binomial=ungebaut)
    assert "Binomial nicht gebaut: 5.000.000 Klauseln liegen über der Grenze von 400.000." in E.verdict_konflikte(z)[1]


def test_verdict_konflikte_ohne_vergleichspartner():
    z = zelle(sinz=[1] * 10, tot=[1] * 10)
    del z["verfahren"]["totalizer"]
    assert E.verdict_konflikte(z)[0] == "info"


def test_kennzahlen_und_vergleich_je_graph():
    z = zelle(sinz=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10], tot=[1, 1, 3, 5, 5, 5, 7, 9, 9, 11])
    kz = E.kennzahlen(z, "sinz")
    assert (kz.laeufe, kz.median, kz.minimum, kz.maximum, kz.abbrueche, kz.klauseln, kz.hilfs) == (10, 5.5, 1, 10, 0, 1500, 700)
    # Graph für Graph (Sinz, Totalizer): (1,1) gleich, (2,1) weniger, (3,3) gleich, (4,5) mehr, (5,5) gleich, (6,5) weniger, (7,7) gleich, (8,9) mehr, (9,9) gleich, (10,11) mehr
    assert E.vergleich_je_graph(z, "sinz", "totalizer") == (2, 5, 3)


def test_zahlenformat():
    assert E.zahl(1190.5) == "1.190,5" and E.zahl(2621) == "2.621" and E.zahl(None) == "–" and E.zahl(9.5) == "9,5" and E.zahl(12.25) == "12,25"
    assert E.zahl_gross(9_999_999) == "9.999.999" and E.zahl_gross(23385332420868688) == "2,3 · 10^16" and E.zahl_gross(10 ** 7) == "1,0 · 10^7"
    assert E.faktor(2.2) == "2,2" and E.faktor(9.94) == "9,9" and E.faktor(10.2) == "10" and E.faktor(683.78) == "684"


# --- Experiment 4 -------------------------------------------------------------------------------------------------------------------------

def _ergebnisse(luecke=(0, 0, 0), falsch=(0, 0, 0)):
    return {v: A.Vollstaendigkeit(729, 233, 233 - l, 480, 480, l, f) for v, l, f in zip(C.VERFAHREN, luecke, falsch)}


def test_verdict_vollstaendigkeit_nennt_die_zahl_der_teilbelegungen():
    kind, text = E.verdict_vollstaendigkeit(_ergebnisse(), 6, 2)
    assert kind == "success" and "Bei n = 6, k = 2 wurden 729 Teilbelegungen geprüft (233 verletzen die Regel, in den übrigen sind insgesamt 480 Eingänge erzwungen)." in text
    assert "so stark wie die Regel selbst" in text


def test_verdict_vollstaendigkeit_luecke_und_falsche_schluesse():
    kind, text = E.verdict_vollstaendigkeit(_ergebnisse(luecke=(0, 3, 0)), 6, 2)
    assert kind == "warning" and "Binomial 0, Sinz-Zähler 3, Totalizer 0" in text and "so stark" not in text
    kind, text = E.verdict_vollstaendigkeit(_ergebnisse(falsch=(0, 0, 2)), 6, 2)
    assert kind == "error" and "2 Schlüsse der Einheitspropagation widersprechen der Regel" in text
