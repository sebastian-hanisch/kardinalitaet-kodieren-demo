"""Einheiten der Demo gegen Handrechnung (DEMO-PLAYBOOK §1b): das Handbeispiel „höchstens 2 von 4“ in drei Kodierungen, Formeln, Namen, Gruppen,
Einheitspropagation, Kontrollpunkte am Dreieck und am Pfad. Die unabhängigen Rechenwege stehen in `test_oracle_kardinalitaet_kodieren.py`."""

from math import comb

import pytest

import kkd_algorithm as A
import kkd_scenario as S

BINOMIAL_TEXT = "(¬x1 ∨ ¬x2 ∨ ¬x3)  (¬x1 ∨ ¬x2 ∨ ¬x4)  (¬x1 ∨ ¬x3 ∨ ¬x4)  (¬x2 ∨ ¬x3 ∨ ¬x4)"
SINZ_TEXT = ("(¬x1 ∨ s11)  (¬s12)  (¬x2 ∨ s21)  (¬s11 ∨ s21)  (¬x2 ∨ ¬s11 ∨ s22)  (¬s12 ∨ s22)  (¬x2 ∨ ¬s12)  (¬x3 ∨ s31)  (¬s21 ∨ s31)  "
             "(¬x3 ∨ ¬s21 ∨ s32)  (¬s22 ∨ s32)  (¬x3 ∨ ¬s22)  (¬x4 ∨ ¬s32)")
TOTALIZER_TEXT = ("(oL1 ∨ ¬x2)  (oL1 ∨ ¬x1)  (oL2 ∨ ¬x1 ∨ ¬x2)  (oR1 ∨ ¬x4)  (oR1 ∨ ¬x3)  (oR2 ∨ ¬x3 ∨ ¬x4)  (oW1 ∨ ¬oR1)  (oW2 ∨ ¬oR2)  (oW1 ∨ ¬oL1)  "
                  "(oW2 ∨ ¬oL1 ∨ ¬oR1)  (oW3 ∨ ¬oL1 ∨ ¬oR2)  (oW2 ∨ ¬oL2)  (oW3 ∨ ¬oL2 ∨ ¬oR1)  (oW3 ∨ ¬oL2 ∨ ¬oR2)  (¬oW3)")


def _text(kod) -> str:
    return "  ".join(A.klausel_text(c, kod.namen) for c in kod.klauseln)


# --- Handbeispiel -------------------------------------------------------------------------------------------------------------------------

def test_handbeispiel_klauseln_und_zahlen(hand):
    """Von Hand (Plan, Handbeispiel): C(4,3) = 4; 2·4·2 + 4 − 3·2 − 1 = 13 Klauseln und (4−1)·2 = 6 Hilfsvariablen; Totalizer 6 + 8 + 1 = 15 Klauseln, 4 + 3 = 7 Hilfsvariablen."""
    assert _text(hand["binomial"]) == BINOMIAL_TEXT
    assert _text(hand["sinz"]) == SINZ_TEXT
    assert _text(hand["totalizer"]) == TOTALIZER_TEXT
    assert [(len(hand[v].klauseln), hand[v].n_gesamt - 4) for v in ("binomial", "sinz", "totalizer")] == [(4, 0), (13, 6), (15, 7)]


def test_formeln_ohne_bau(hand):
    assert [(A.klauselzahl(v, 4, 2), A.hilfsvariablen(v, 4, 2)) for v in ("binomial", "sinz", "totalizer")] == [(4, 0), (13, 6), (15, 7)]
    assert comb(25, 6) == 177100 == A.klauselzahl("binomial", 25, 5)
    assert (A.klauselzahl("sinz", 25, 5), A.hilfsvariablen("sinz", 25, 5)) == (259, 120)
    assert (A.klauselzahl("totalizer", 25, 5), A.hilfsvariablen("totalizer", 25, 5)) == (279, 85)


def test_namen_und_gruppen_des_handbeispiels(hand):
    assert [hand["sinz"].namen[v] for v in range(5, 11)] == ["s11", "s12", "s21", "s22", "s31", "s32"]
    assert [hand["totalizer"].namen[v] for v in range(5, 12)] == ["oL1", "oL2", "oR1", "oR2", "oW1", "oW2", "oW3"]
    assert hand["totalizer"].gruppen == ["Addierer links"] * 3 + ["Addierer rechts"] * 3 + ["Wurzel"] * 8 + ["Schranke"]
    assert hand["sinz"].gruppen == ["Eingang 1"] * 2 + ["Eingang 2"] * 5 + ["Eingang 3"] * 5 + ["Eingang 4"]
    assert set(hand["binomial"].gruppen) == {"verbotene Teilmenge"}


def test_totalizer_tiefer_baum_namen_und_gruppen():
    """n = 8, k = 3: Blätter x1..x4 | x5..x8, darunter links-links usw.; die Namen sind eindeutig, jede Klausel hat eine Gruppe."""
    kod = A.kodierung(8, 3, "totalizer")
    assert len(set(kod.namen.values())) == len(kod.namen) == kod.n_gesamt
    assert len(kod.gruppen) == len(kod.klauseln) == A.klauselzahl("totalizer", 8, 3)
    assert "Addierer links-rechts" in kod.gruppen and kod.gruppen[-1] == "Schranke" and kod.namen[kod.n_gesamt] == "oW4"


def test_randfaelle_der_kodierung():
    assert A.kodierung(4, 4, "sinz").klauseln == [] and A.kodierung(4, 9, "totalizer").klauseln == []      # k >= n: nie verletzt
    assert A.klauselzahl("binomial", 4, 4) == 0 and A.hilfsvariablen("totalizer", 4, 4) == 0
    for v in ("binomial", "sinz", "totalizer"):
        kod = A.kodierung(3, 0, v)                                            # k = 0: alle Eingänge falsch
        assert kod.klauseln == [(-1,), (-2,), (-3,)] and kod.gruppen == ["Einheitsklausel"] * 3 and kod.n_gesamt == 3
        assert (A.klauselzahl(v, 3, 0), A.hilfsvariablen(v, 3, 0)) == (3, 0)
    with pytest.raises(ValueError):
        A.kodierung(3, 1, "unbekannt")
    with pytest.raises(ValueError):
        A.kodierung(0, 1, "sinz")


def test_klausel_text_und_zustand():
    namen = {1: "x1", 2: "x2", 3: "s11"}
    assert A.klausel_text((-1, 3), namen) == "(¬x1 ∨ s11)" and A.klausel_text((), namen) == "()"
    assert A.klauselzustand((-1, 3), {1: True}) == "Einheit"
    assert A.klauselzustand((-1, 3), {1: True, 3: False}) == "verletzt"
    assert A.klauselzustand((-1, 3), {1: False}) == "erfüllt"
    assert A.klauselzustand((1, 2, 3), {}) == "offen"


# --- Einheitspropagation ------------------------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("verfahren, schluesse", [("binomial", 2), ("sinz", 8), ("totalizer", 9)])
def test_propagation_x1_x2_wahr_setzt_x3_x4_falsch(hand, verfahren, schluesse):
    """Von Hand (Sinz): s11, s21, s22, s31, s32 wahr, s12 falsch (Einheit), dann x3 und x4 falsch: 8 Schlüsse; Totalizer 9 (siehe Plan); binomial 2."""
    kod = hand[verfahren]
    p = A.propagiere(kod.klauseln, kod.n_gesamt, {1: True, 2: True})
    assert p.konflikt is None and len(p.schritte) == schluesse
    assert (p.belegung[3], p.belegung[4]) == (False, False)
    assert {l for l, _ in p.schritte if abs(l) <= 4} == {-3, -4}


def test_propagation_binomial_nennt_die_ausloesende_klausel(hand):
    kod = hand["binomial"]
    p = A.propagiere(kod.klauseln, 4, {1: True, 2: True})
    grund = {l: g for l, g in p.schritte}
    assert grund[-3] == 0 and grund[-4] == 1       # (¬x1 ∨ ¬x2 ∨ ¬x3) und (¬x1 ∨ ¬x2 ∨ ¬x4)


@pytest.mark.parametrize("verfahren", ["binomial", "sinz", "totalizer"])
def test_propagation_drei_wahre_eingaenge_ist_ein_konflikt(hand, verfahren):
    kod = hand[verfahren]
    p = A.propagiere(kod.klauseln, kod.n_gesamt, {1: True, 2: True, 3: True})
    assert p.konflikt is not None and A.klauselzustand(kod.klauseln[p.konflikt], p.belegung) == "verletzt"
    assert A.propagiere(kod.klauseln, kod.n_gesamt, {1: True, 2: True, 3: False}).konflikt is None


def test_propagation_widerspruch_zwischen_annahme_und_einheitsklausel():
    kod = A.kodierung(3, 0, "sinz")                # (¬x1) (¬x2) (¬x3)
    p = A.propagiere(kod.klauseln, 3, {2: True})
    assert p.konflikt == 1 and p.belegung == {2: True}


def test_propagation_ohne_annahmen_und_leere_klausel():
    assert A.propagiere([(1, 2)], 2, {}).belegung == {} and A.propagiere([(1,)], 1, {}).belegung == {1: True}
    assert A.propagiere([(1,), ()], 1, {}).konflikt == 1


def test_propagator_ist_wiederverwendbar(hand):
    kod = hand["sinz"]
    prop = A.Propagator(kod.klauseln, kod.n_gesamt)
    erst = prop.lauf({1: True, 2: True})
    assert prop.lauf({1: True, 2: True}) == erst and prop.lauf({}).belegung == {-l if False else abs(l): l > 0 for l, _ in prop.lauf({}).schritte}


# --- Semantik und Vollständigkeit ----------------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("verfahren", ["binomial", "sinz", "totalizer"])
def test_semantik_aller_16_eingaben(verfahren):
    assert A.semantik_pruefen(verfahren, 4, 2) == (16, 0)


def test_erwartung_aus_der_regel():
    assert A.erwartung((True, True, None, None), 2) == (False, {3, 4})
    assert A.erwartung((True, True, True, None), 2) == (True, set())
    assert A.erwartung((True, None, False, None), 2) == (False, set())


@pytest.mark.parametrize("verfahren", ["binomial", "sinz", "totalizer"])
def test_vollstaendigkeit_handbeispiel_81_teilbelegungen(verfahren):
    """Von Hand gezählt: Verletzungen = Teilbelegungen mit ≥ 3 wahren Eingängen: Σ_{w≥3} C(4,w)·2^(4−w) (alle w wahre, Rest falsch oder offen) = 8 + 1 = 9;
    erzwungene Eingänge: genau 2 wahre, 2 offene: C(4,2) = 6 Teilbelegungen mit 2 wahren, 2 falschen/offenen ... gezählt als 24 offene Eingänge."""
    r = A.vollstaendigkeit(verfahren, 4, 2, A.alle_teilbelegungen(4))
    assert r.teilbelegungen == 81 and r.verletzungen == 9 == r.verletzung_erkannt
    assert r.erzwungen == 24 == r.erzwungen_erkannt and r.mit_luecke == 0 and r.falsch_geschlossen == 0


def test_vollstaendigkeit_zaehlt_eine_luecke():
    """Eine absichtlich unvollständige Kodierung (nur die Hälfte der Klauseln) muss als Lücke auffallen; zwei Teilbelegungen von Hand."""
    kod = A.kodierung(4, 2, "binomial")
    prop = A.Propagator(kod.klauseln[:1], 4)         # nur (¬x1 ∨ ¬x2 ∨ ¬x3)
    p = prop.lauf({1: True, 2: True})
    assert p.belegung.get(3) is False and 4 not in p.belegung     # x4 bleibt offen: die Regel würde x4 = falsch erzwingen


def test_teilbelegungen_zufall_deterministisch():
    a = A.zufalls_teilbelegungen(10, 50, 35)
    assert a == A.zufalls_teilbelegungen(10, 50, 35) and a != A.zufalls_teilbelegungen(10, 50, 36)
    assert all(len(b) == 10 and set(b) <= {None, False, True} for b in a)
    assert len(list(A.alle_teilbelegungen(6))) == 729


# --- Kontrollpunkte -----------------------------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("verfahren", ["binomial", "sinz", "totalizer"])
def test_dreieck_optimum_zwei_von_hand(verfahren):
    """Dreieck: jede Kante braucht einen Kontrollpunkt an einem Ende; mit einem Auftrag bleibt eine Kante offen (k = 1 unerfüllbar), mit zwei sind alle drei gedeckt."""
    n, kanten = S.DREIECK
    assert A.optimum_aufzaehlung(n, kanten) == 2
    assert A.messe_lauf(n, kanten, 1, verfahren, 1000)["antwort"] is False
    r = A.messe_lauf(n, kanten, 2, verfahren, 1000)
    assert r["antwort"] is True and r["modell_ok"] is True


def test_pfad_mit_drei_knoten_optimum_eins():
    n, kanten = S.PFAD3
    assert A.optimum_aufzaehlung(n, kanten) == 1
    assert A.ist_ueberdeckung(kanten, [1]) and not A.ist_ueberdeckung(kanten, [0])
    f = A.kontrollpunkte(n, kanten, 1, "sinz")
    assert f.klauseln[:2] == [(1, 2), (2, 3)] and f.n_kanten == 2 and len(f.klauseln) == 2 + A.klauselzahl("sinz", 3, 1)


def test_graph_deterministisch_und_kantenzahl():
    assert A.graph(25, 3.0, 600) == A.graph(25, 3.0, 600) and len(A.graph(25, 3.0, 600)) == 38      # round(37,5) = 38
    assert len(A.graph(40, 3.5, 601)) == 70 and len(A.graph(60, 3.0, 602)) == 90
    assert S.beschreibung(25, 3.0) == "25 Aufträge, 38 Unverträglichkeiten (mittlerer Grad 3,0)"


def test_optimum_aus_der_datei_und_fehlender_eintrag():
    assert A.optimum(25, 3.0, 600) == 12
    with pytest.raises(KeyError):
        A.optimum(26, 3.0, 600)
    with pytest.raises(KeyError):
        A.optimum(25, 3.0, 1)
