"""Randfälle, an denen Kernroutinen erfahrungsgemäß brechen (DEMO-PLAYBOOK §12): n = 1, n = 2, k = 0, k ≥ n, Graph ohne Kanten, vollständiger Graph,
Konfliktbudget erreicht (Antwort „unbekannt“ wird nie als unerfüllbar angezeigt), Grenzen inklusive."""

import itertools

import pytest

import kkd_algorithm as A
import kkd_constants as C
import kkd_evaluation as E

VERFAHREN = ("binomial", "sinz", "totalizer")


@pytest.mark.parametrize("verfahren", VERFAHREN)
def test_genau_zwei_eingaenge_k_gleich_1(verfahren):
    """n = 2, k = 1: höchstens einer von zwei. Binomial (¬x1 ∨ ¬x2); Sinz 3 Klauseln, Totalizer 3 + 1 Schranke."""
    kod = A.kodierung(2, 1, verfahren)
    assert A.klauselzahl(verfahren, 2, 1) == len(kod.klauseln)
    for bits in itertools.product((False, True), repeat=2):
        assert A.erfuellbar(kod.klauseln, kod.n_gesamt, {1: bits[0], 2: bits[1]}) == (sum(bits) <= 1)
    assert A.klauselzahl("binomial", 2, 1) == 1 and A.kodierung(2, 1, "binomial").klauseln == [(-1, -2)]


@pytest.mark.parametrize("verfahren", VERFAHREN)
def test_ein_eingang(verfahren):
    assert A.kodierung(1, 1, verfahren).klauseln == []                              # k ≥ n
    assert A.kodierung(1, 0, verfahren).klauseln == [(-1,)]                         # k = 0: der Eingang ist falsch
    assert A.propagiere([(-1,)], 1, {1: True}).konflikt == 0


def test_grenzen_k_gleich_n_minus_1_und_k_gleich_n_inklusive():
    for v in VERFAHREN:
        assert A.klauselzahl(v, 5, 5) == 0 and A.klauselzahl(v, 5, 4) > 0                # k = n − 1 ist die letzte Grenze mit Klauseln
        assert A.erfuellbar(*(lambda k: (k.klauseln, k.n_gesamt))(A.kodierung(5, 4, v)), {i: True for i in range(1, 6)}) is False
        assert A.erfuellbar(*(lambda k: (k.klauseln, k.n_gesamt))(A.kodierung(5, 5, v)), {i: True for i in range(1, 6)}) is True


def test_reglergrenzen_der_ansicht_von_hand_erzeugen_gueltige_kodierungen():
    for n in range(C.E1_N[0], C.E1_N[1] + 1):
        for k in range(C.E1_K[0], C.E1_K[1] + 1):
            for v in VERFAHREN:
                kod = A.kodierung(n, k, v)
                assert len(kod.klauseln) == A.klauselzahl(v, n, k) and kod.n_gesamt - n == A.hilfsvariablen(v, n, k)


@pytest.mark.parametrize("verfahren", VERFAHREN)
def test_graph_ohne_kanten_k_null_ist_erfuellbar(verfahren):
    r = A.messe_lauf(4, [], 0, verfahren, 100)
    assert r["antwort"] is True and r["modell_ok"] is True and A.optimum_aufzaehlung(4, []) == 0


@pytest.mark.parametrize("verfahren", VERFAHREN)
def test_vollstaendiger_graph_braucht_n_minus_1_kontrollpunkte(verfahren):
    n = 6
    kanten = [(a, b) for a in range(n) for b in range(a + 1, n)]
    assert A.optimum_aufzaehlung(n, kanten) == n - 1
    assert A.messe_lauf(n, kanten, n - 2, verfahren, 1000)["antwort"] is False
    assert A.messe_lauf(n, kanten, n - 1, verfahren, 1000)["antwort"] is True


def test_k_null_mit_kanten_ist_unerfuellbar():
    assert A.messe_lauf(3, [(0, 1)], 0, "sinz", 100)["antwort"] is False


def test_budget_erreicht_antwortet_unbekannt_und_nie_unerfuellbar():
    """Ein Graph, der mehr als zwei Konflikte braucht (n = 60 am Optimum − 1), mit Budget 2: Antwort None, die Konfliktzahl liegt beim Budget."""
    n, grad, seed = 60, 3.0, 600
    kanten, k = A.graph(n, grad, seed), A.optimum(n, grad, seed) - 1
    r = A.messe_lauf(n, kanten, k, "sinz", 2)
    assert r["antwort"] is None and r["konflikte"] >= 2 and r["modell_ok"] is None


def test_abbruch_wird_im_verdikt_nie_als_unerfuellbar_gelesen_und_zaehlt_mit_dem_budget():
    z = E.messe_zelle(60, 3.0, "Optimum − 1", None, ("sinz", "totalizer"), 2, seeds=C.GRAPH_SEEDS[:3])
    assert all(a is None for v in z["verfahren"].values() for a in v["antwort"])
    kz = E.kennzahlen(z, "sinz")
    assert kz.abbrueche == 3 and kz.median == 2 and kz.falsche_antworten == 0                # Abbrüche zählen mit dem Budget (2), sind keine falschen Antworten
    kind, text = E.verdict_konflikte(z)
    assert "Abbrüche am Budget (2 Konflikte): Sinz 3, Totalizer 3" in text and "untere Schranken" in text


def test_messzelle_bei_k_ab_n_hat_keine_klauseln_des_zaehlers():
    r = A.messe_lauf(4, [(0, 1), (2, 3)], 4, "totalizer", 100)
    assert r["klauseln"] == 2 and r["hilfs"] == 0 and r["antwort"] is True


def test_binomiale_kodierung_wird_ueber_der_grenze_nicht_gebaut():
    z = E.messe_zelle(25, 3.0, "Optimum", None, ("binomial",), 100, seeds=C.GRAPH_SEEDS[:2])
    je = z["verfahren"]["binomial"]
    assert je["gebaut"] is False and je["konflikte"] == [None, None] and je["antwort"] == [None, None]
    assert je["klauseln"] == [38 + A.klauselzahl("binomial", 25, 12), 38 + A.klauselzahl("binomial", 25, 12)]
    assert E.kennzahlen(z, "binomial").gebaut is False


def test_k_je_graph_in_den_drei_modi():
    assert E.k_je_graph(25, 3.0, "Optimum", None, C.GRAPH_SEEDS[:3]) == [12, 12, 13]
    assert E.k_je_graph(25, 3.0, "Optimum − 1", None, C.GRAPH_SEEDS[:3]) == [11, 11, 12]
    assert E.k_je_graph(25, 3.0, "fester Wert k", 5, C.GRAPH_SEEDS[:3]) == [5, 5, 5]
    assert E.zellen_schluessel(25, 3.0, "Optimum − 1", None) == "25|3.0|opt-1" and E.zellen_schluessel(25, 3.0, "fester Wert k", 5) == "25|3.0|k5"
