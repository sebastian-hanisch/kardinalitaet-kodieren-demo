"""Orakel-Tests (ORACLE-PLAYBOOK §5): die Kernroutinen gegen einen anderen Rechenweg.

* Semantik der drei Kodierungen: Aufzählung aller Hilfsvariablen-Belegungen (reines Python, Handbeispiel-Verfahren) und OR-Tools CP-SAT;
* Einheitspropagation: eine naive Fixpunkt-Schleife über alle Klauseln gegen den zählerbasierten `Propagator`; die Folgerungen der Regel gegen die Aufzählung aller Vervollständigungen;
* Antwort des Lösers auf „Kontrollpunkte höchstens k“ gegen CP-SAT (`AddBoolOr` und `Sum ≤ k`), das Optimum gegen Aufzählung und CP-SAT;
* Formeln: Sinz 2nk + n − 3k − 1 (Sinz 2005), (n − 1)k, C(n, k + 1) und die Totalizer-Rekursion gegen den Aufbau;
* Eigenschaften: Randfälle k = 0, k ≥ n, n = 1; „mindestens“ und „genau“; Umbenennen der Aufträge ändert die Antwort nie.
Der große Lauf (200 Zufallsgraphen) steht nur im Scratch-Lauf, hier die kleine Fassung."""

import itertools
from math import comb

import pytest

import kkd_algorithm as A
import kkd_constants as C
import kkd_kodierung as K
from kkd_rng import SplitMix64

cp_model = pytest.importorskip("ortools.sat.python.cp_model")
VERFAHREN = ("binomial", "sinz", "totalizer")


def _wert(l, val):
    return val[abs(l)] if l > 0 else not val[abs(l)]


# --------------------------------------------------------------------------------------------------------- Semantik: Aufzählung der Hilfsvariablen


@pytest.mark.parametrize("verfahren", VERFAHREN)
def test_semantik_gegen_aufzaehlung_aller_hilfsvariablen(verfahren):
    """Für jede Eingabe: erfüllbar mit Hilfsvariablen genau dann, wenn höchstens k wahr sind (alle Belegungen der Hilfsvariablen ausprobiert)."""
    geprueft = 0
    for n in range(1, 7):
        for k in range(0, n + 1):
            kod = A.kodierung(n, k, verfahren)
            hilfs = list(range(n + 1, kod.n_gesamt + 1))
            if len(hilfs) > 12:
                continue
            for bits in itertools.product((False, True), repeat=n):
                val = {i + 1: b for i, b in enumerate(bits)}
                ok = any(all(any(_wert(l, {**val, **dict(zip(hilfs, h))}) for l in c) for c in kod.klauseln)
                         for h in itertools.product((False, True), repeat=len(hilfs)))
                assert ok == (sum(bits) <= k), (verfahren, n, k, bits)
                geprueft += 1
    assert geprueft > 500


@pytest.mark.parametrize("verfahren", VERFAHREN)
def test_semantik_gegen_cpsat(verfahren):
    for n, k in [(4, 1), (4, 2), (5, 2), (6, 1), (6, 3)]:
        kod = A.kodierung(n, k, verfahren)
        for bits in itertools.product((False, True), repeat=n):
            m = cp_model.CpModel()
            x = [None] + [m.NewBoolVar(f"v{i}") for i in range(1, kod.n_gesamt + 1)]
            for c in kod.klauseln:
                m.AddBoolOr([x[l] if l > 0 else x[-l].Not() for l in c])
            for i, b in enumerate(bits):
                m.Add(x[i + 1] == int(b))
            s = cp_model.CpSolver()
            s.parameters.num_workers = 1
            assert (s.Solve(m) in (cp_model.OPTIMAL, cp_model.FEASIBLE)) == (sum(bits) <= k), (verfahren, n, k, bits)


def test_eigene_semantikpruefung_stimmt_mit_der_aufzaehlung_ueberein():
    for verfahren in VERFAHREN:
        for n, k in [(2, 1), (5, 2), (6, 4), (8, 3)]:
            assert A.semantik_pruefen(verfahren, n, k) == (2 ** n, 0), (verfahren, n, k)


# ------------------------------------------------------------------------------------------------------------------- Einheitspropagation


def naive_up(klauseln, fixed):
    """Naive Einheitspropagation (Fixpunkt über alle Klauseln, wie im Handbeispiel): (Belegung, Konflikt?)."""
    val = dict(fixed)
    wieder = True
    while wieder:
        wieder = False
        for c in klauseln:
            offen, erfuellt = [], False
            for l in c:
                w = val.get(abs(l))
                if w is None:
                    offen.append(l)
                elif w == (l > 0):
                    erfuellt = True
                    break
            if erfuellt:
                continue
            if not offen:
                return val, True
            if len(offen) == 1:
                val[abs(offen[0])] = offen[0] > 0
                wieder = True
    return val, False


@pytest.mark.parametrize("verfahren", VERFAHREN)
def test_propagator_gegen_naive_fixpunktschleife(verfahren):
    for n, k in [(4, 2), (5, 2), (5, 3), (6, 1)]:
        kod = A.kodierung(n, k, verfahren)
        prop = A.Propagator(kod.klauseln, kod.n_gesamt)
        for bel in A.alle_teilbelegungen(n):
            fixed = {i + 1: b for i, b in enumerate(bel) if b is not None}
            val, konflikt = naive_up(kod.klauseln, fixed)
            p = prop.lauf(fixed)
            assert (p.konflikt is not None) == konflikt, (verfahren, n, k, bel)
            if not konflikt:
                assert p.belegung == val, (verfahren, n, k, bel)


def test_folgerungen_der_regel_gegen_aufzaehlung_der_vervollstaendigungen():
    """Die geschlossene Form von `erwartung` gegen die Aufzählung aller Vervollständigungen mit höchstens k wahren Eingängen."""
    for n in range(1, 7):
        for k in range(0, n + 1):
            for bel in A.alle_teilbelegungen(n):
                voll = [b for b in itertools.product((False, True), repeat=n)
                        if all(f is None or f == x for f, x in zip(bel, b)) and sum(b) <= k]
                verletzt, erzwungen = A.erwartung(bel, k)
                assert verletzt == (not voll), (n, k, bel)
                if voll:
                    fest_falsch = {i + 1 for i in range(n) if bel[i] is None and all(not b[i] for b in voll)}
                    fest_wahr = {i + 1 for i in range(n) if bel[i] is None and all(b[i] for b in voll)}
                    assert erzwungen == fest_falsch and not fest_wahr, (n, k, bel)


@pytest.mark.parametrize("verfahren", VERFAHREN)
def test_einheitspropagation_ist_vollstaendig_n6_k2(verfahren):
    """Experiment 4 gegen die Aufzählung: keine übersehene Folgerung, keine falsche (alle 729 Teilbelegungen)."""
    r = A.vollstaendigkeit(verfahren, 6, 2, A.alle_teilbelegungen(6))
    assert r.teilbelegungen == 729 and r.mit_luecke == 0 and r.falsch_geschlossen == 0 and r.verletzung_erkannt == r.verletzungen


# ----------------------------------------------------------------------------------------------------------------------------------- Formeln


def test_sinz_formeln_gegen_den_aufbau_alle_2_le_k_lt_n_le_30():
    for n in range(3, 31):
        for k in range(2, n):
            pool = K.Hilfsvariablen(n)
            kl = K.hoechstens_sinz(list(range(1, n + 1)), k, pool)
            assert len(kl) == 2 * n * k + n - 3 * k - 1 == A.klauselzahl("sinz", n, k), (n, k)
            assert pool.n - n == (n - 1) * k == A.hilfsvariablen("sinz", n, k), (n, k)


def test_binomial_und_totalizer_formeln_gegen_den_aufbau():
    for n in range(1, 17):
        for k in range(0, n + 2):
            pool = K.Hilfsvariablen(n)
            assert len(K.hoechstens_binomial(list(range(1, n + 1)), k, pool)) == (comb(n, k + 1) if k < n else 0) == A.klauselzahl("binomial", n, k)
            pool = K.Hilfsvariablen(n)
            kl = K.hoechstens_totalizer(list(range(1, n + 1)), k, pool)
            assert (len(kl), pool.n - n) == (A.klauselzahl("totalizer", n, k), A.hilfsvariablen("totalizer", n, k)), (n, k)


def test_gebaute_zahl_gleich_formel_in_der_wachstumsansicht():
    import kkd_evaluation as E
    for n, k in [(25, 5), (10, 3), (30, 8)]:
        for v in VERFAHREN:
            gebaut = E.gebaute_klauselzahl(v, n, k)
            assert gebaut is None or gebaut == A.klauselzahl(v, n, k)
    assert E.gebaute_klauselzahl("binomial", 30, 5) is None                      # C(30, 6) = 593 775 > 400 000
    assert E.gebaute_klauselzahl("binomial", 25, 5) == 177100


# ------------------------------------------------------------------------------------------------------------------ Kontrollpunkte gegen CP-SAT


def cpsat_loesbar(n, kanten, k):
    m = cp_model.CpModel()
    x = [m.NewBoolVar(f"x{i}") for i in range(n)]
    for a, b in kanten:
        m.AddBoolOr([x[a], x[b]])
    m.Add(sum(x) <= k)
    s = cp_model.CpSolver()
    s.parameters.num_workers = 1
    return s.Solve(m) in (cp_model.OPTIMAL, cp_model.FEASIBLE)


def test_antwort_des_loesers_gegen_cpsat_auf_30_graphen():
    for i in range(30):
        n = 8 + i % 7
        kanten = A.graph(n, (3.0, 3.5)[i % 2], 5000 + i)
        opt = A.optimum_aufzaehlung(n, kanten)
        for k in (opt - 1, opt):
            if k < 0:
                continue
            erwartet = cpsat_loesbar(n, kanten, k)
            assert erwartet == (k >= opt)
            for v in VERFAHREN:
                r = A.messe_lauf(n, kanten, k, v, 100000)
                assert r["antwort"] is erwartet, (i, k, v)
                if erwartet:
                    assert r["modell_ok"] is True, (i, k, v)


def test_optimum_aufzaehlung_gegen_cpsat_bis_n_14():
    for i in range(12):
        n = 6 + i
        kanten = A.graph(n, 3.0, 7000 + i)
        opt = A.optimum_aufzaehlung(n, kanten)
        assert cpsat_loesbar(n, kanten, opt) and (opt == 0 or not cpsat_loesbar(n, kanten, opt - 1))


def test_eingefrorene_optima_gegen_cpsat():
    """k = Optimum ist lösbar, k = Optimum − 1 nicht: für alle 100 Graphen der Datei (5 Größen, 2 Grade, 10 Seeds)."""
    zaehler = 0
    for n in C.E3_N:
        for grad in C.E3_GRAD:
            for seed in C.GRAPH_SEEDS:
                opt, kanten = A.optimum(n, grad, seed), A.graph(n, grad, seed)
                assert cpsat_loesbar(n, kanten, opt) and not cpsat_loesbar(n, kanten, opt - 1), (n, grad, seed)
                zaehler += 1
    assert zaehler == 100


def test_optima_stimmen_mit_aufzaehlung_fuer_kleine_graphen_der_datei_ueberein():
    """Aufzählung (n bis 20) braucht Graphen dieser Größe: die Datei hat n ≥ 25, deshalb hier eine obere und untere Schranke der Datei, die ohne Löser prüfbar ist:
    Gierige Überdeckung ≥ Optimum ≥ Größe einer maximalen Paarung (Kanten ohne gemeinsamen Knoten)."""
    for n, grad in [(25, 3.0), (30, 3.5), (40, 3.0)]:
        for seed in C.GRAPH_SEEDS:
            kanten = A.graph(n, grad, seed)
            gewaehlt, paarung = set(), 0
            for a, b in kanten:                                    # maximale Paarung (greedy) und die Überdeckung durch beide Endpunkte
                if a not in gewaehlt and b not in gewaehlt:
                    gewaehlt |= {a, b}
                    paarung += 1
            assert A.ist_ueberdeckung(kanten, gewaehlt)
            assert paarung <= A.optimum(n, grad, seed) <= 2 * paarung, (n, grad, seed)


# ----------------------------------------------------------------------------------------------------------------------------- Eigenschaften


@pytest.mark.parametrize("verfahren", VERFAHREN)
def test_mindestens_und_genau_gegen_aufzaehlung(verfahren):
    n = 5
    for k in range(0, n + 2):
        for fn, soll in ((K.mindestens, lambda s: s >= k), (K.genau, lambda s: s == k)):
            pool = K.Hilfsvariablen(n)
            kl = fn(list(range(1, n + 1)), k, pool, verfahren)
            for bits in itertools.product((False, True), repeat=n):
                feste = {i + 1: b for i, b in enumerate(bits)}
                assert A.erfuellbar(kl, pool.n, feste) == soll(sum(bits)), (verfahren, fn.__name__, k, bits)


@pytest.mark.parametrize("verfahren", VERFAHREN)
def test_umbenennen_der_auftraege_aendert_die_antwort_nie(verfahren):
    rng = SplitMix64(11)
    for seed in range(6):
        n = 12
        kanten = A.graph(n, 3.0, 300 + seed)
        perm = list(range(n))
        rng.shuffle(perm)
        umbenannt = sorted((min(perm[a], perm[b]), max(perm[a], perm[b])) for a, b in kanten)
        opt = A.optimum_aufzaehlung(n, kanten)
        assert A.optimum_aufzaehlung(n, umbenannt) == opt
        for k in (opt - 1, opt):
            assert A.messe_lauf(n, kanten, k, verfahren, 10000)["antwort"] is A.messe_lauf(n, umbenannt, k, verfahren, 10000)["antwort"] is (k >= opt)


def test_randfaelle_n1_und_k_gleich_n_gegen_aufzaehlung():
    assert A.erfuellbar(*(lambda kod: (kod.klauseln, kod.n_gesamt))(A.kodierung(1, 0, "sinz")), {1: True}) is False
    for v in VERFAHREN:
        kod = A.kodierung(1, 1, v)
        assert kod.klauseln == [] and A.erfuellbar(kod.klauseln, kod.n_gesamt, {1: True}) is True
