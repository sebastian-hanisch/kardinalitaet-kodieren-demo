"""Zweige: jede Variante der Messreihe wird wirklich ausgeführt (keine Nullspalte) und weicht von ihrer Nachbarvariante ab (DEMO-PLAYBOOK §0, Memory „Nullspalte = Bug-Signal“)."""

import pytest

import kkd_algorithm as A
import kkd_constants as C
import kkd_evaluation as E


@pytest.fixture(scope="module")
def zellen():
    d = E.lade_messungen()["zellen"]
    assert len(d) == len(C.REFERENZ_ZELLEN)
    return d


def test_keine_nullspalte_in_den_vorgerechneten_zellen(zellen):
    for key, z in zellen.items():
        for v in ("sinz", "totalizer"):
            assert any(c > 0 for c in z["verfahren"][v]["konflikte"]), (key, v)


def test_sinz_und_totalizer_weichen_in_jeder_zelle_voneinander_ab(zellen):
    for key, z in zellen.items():
        assert z["verfahren"]["sinz"]["konflikte"] != z["verfahren"]["totalizer"]["konflikte"], key
        assert z["verfahren"]["sinz"]["klauseln"] != z["verfahren"]["totalizer"]["klauseln"], key


def test_die_modi_weichen_voneinander_ab(zellen):
    for n in C.E3_N:
        for g in C.E3_GRAD:
            a, b = zellen[f"{n}|{g}|opt"], zellen[f"{n}|{g}|opt-1"]
            assert a["k"] != b["k"] and a["erwartet"] != b["erwartet"] and a["verfahren"]["sinz"]["konflikte"] != b["verfahren"]["sinz"]["konflikte"], (n, g)


def test_alle_antworten_der_vorgerechneten_zellen_stimmen_mit_der_erwartung_und_cpsat_optimum_ueberein(zellen):
    for key, z in zellen.items():
        for v, je in z["verfahren"].items():
            kz = E.kennzahlen(z, v)
            if kz.gebaut:
                assert kz.falsche_antworten == 0 and kz.abbrueche == 0, (key, v)
                assert all(a == e for a, e in zip(je["antwort"], z["erwartet"])), (key, v)
                assert all(m for a, m in zip(je["antwort"], je["modell_ok"]) if a is True), (key, v)


def test_die_beiden_zaehler_haben_je_graph_unterschiedliche_groesse():
    for v in ("sinz", "totalizer"):
        assert A.klauselzahl(v, 40, 19) > 0
    assert A.klauselzahl("sinz", 40, 19) != A.klauselzahl("totalizer", 40, 19) and A.hilfsvariablen("sinz", 40, 19) != A.hilfsvariablen("totalizer", 40, 19)
