"""Inhalt der App (AppTest): Experiment 1 mit Handbeispiel, Kodierungswechsel, Konflikt, k ≥ n; Experiment 2 bis 4 mit den Verdikten; Permalink."""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

import kkd_constants as C

APP = str(Path(__file__).resolve().parent.parent / "app.py")


def _app(**query) -> AppTest:
    at = AppTest.from_file(APP, default_timeout=180)
    for k, v in query.items():
        at.query_params[k] = v
    at.run()
    assert not at.exception, [str(e) for e in at.exception]
    return at


def _metrik(at) -> dict:
    return {m.label: m.value for m in at.metric}


def _texte(at, art: str) -> list:
    return [e.value for e in getattr(at, art)]


def test_handbeispiel_zahlen_in_der_ansicht_von_hand():
    at = _app()
    assert _metrik(at) == {"Klauseln": "13", "Hilfsvariablen": "6"}
    assert any("Abweichungen: 0" in c.value and "alle 16 Belegungen" in c.value for c in at.caption)


@pytest.mark.parametrize("verfahren, kl, hv", [("Binomial", "4", "0"), ("Sinz-Zähler", "13", "6"), ("Totalizer", "15", "7")])
def test_wechsel_der_kodierung_aendert_die_zahlen(verfahren, kl, hv):
    at = _app()
    at.radio(key="e1_verfahren").set_value(verfahren).run()
    assert not at.exception and _metrik(at) == {"Klauseln": kl, "Hilfsvariablen": hv}


def test_preset_handbeispiel_setzt_x1_x2_und_zeigt_die_propagation():
    at = _app()
    at.sidebar.button(key="preset_Handbeispiel").click().run()
    assert [at.selectbox(key=f"e1_x{i}").value for i in (1, 2, 3, 4)] == ["wahr", "wahr", "offen", "offen"]
    erfolg = _texte(at, "success")
    assert any(t.startswith("Einheitspropagation: ¬x3, ¬x4 (8 Schlüsse, davon 2 an Eingängen).") for t in erfolg), erfolg


def test_drei_wahre_eingaenge_sind_ein_konflikt():
    at = _app()
    for i in (1, 2, 3):
        at.selectbox(key=f"e1_x{i}").set_value("wahr")
    at.run()
    fehler = _texte(at, "error")
    assert len(fehler) == 1 and fehler[0].startswith("**Konflikt:**") and "Mehr als 2 Eingänge wären wahr" in fehler[0]


def test_k_ab_n_braucht_keine_klausel():
    at = _app()
    at.slider(key="e1_n").set_value(3)
    at.slider(key="e1_k").set_value(5).run()
    assert not at.exception and _metrik(at) == {"Klauseln": "0", "Hilfsvariablen": "0"}
    assert any("immer erfüllt" in t for t in _texte(at, "info"))


def test_n_8_k_7_ist_bedienbar():
    at = _app()
    at.slider(key="e1_n").set_value(8)
    at.slider(key="e1_k").set_value(7).run()
    assert not at.exception


def test_experiment_2_verdikt_am_standardpunkt():
    at = _app()
    texte = _texte(at, "success") + _texte(at, "info")
    assert any("Bei n = 25, k = 5 hat die binomiale Kodierung 177.100 Klauseln, der Sinz-Zähler 259 (120 Hilfsvariablen), der Totalizer 279 (85 Hilfsvariablen)." in t
               for t in texte)


def test_experiment_2_regler_aendern_das_verdikt():
    at = _app()
    at.slider(key="e2_n").set_value(30)
    at.slider(key="e2_k").set_value(5).run()
    assert any("Bei n = 30, k = 5 hat die binomiale Kodierung 593.775 Klauseln" in t for t in _texte(at, "success") + _texte(at, "info"))


def test_experiment_4_nennt_die_zahl_der_teilbelegungen():
    at = _app()
    texte = _texte(at, "success") + _texte(at, "warning") + _texte(at, "error")
    assert any("Bei n = 6, k = 2 wurden 729 Teilbelegungen geprüft" in t for t in texte)
    assert any("Bei n = 10, k = 3 wurden 5.000 Teilbelegungen geprüft" in t for t in texte)


def test_experiment_3_zeigt_die_vorgerechnete_zelle_des_standards_und_das_verdikt():
    at = _app()
    texte = _texte(at, "success") + _texte(at, "info") + _texte(at, "warning")
    assert any(t.startswith("Am Optimum (erfüllbar), n = 25, 10 Graphen:") and "von 10 Graphen hat der Totalizer weniger Konflikte" in t for t in texte)
    assert any("Vorgerechnet, nicht live" in c.value for c in at.caption)


def test_k_regler_waehlt_den_modus_fester_wert():
    at = _app()
    at.slider(key="e3_k").set_value(8).run()
    assert at.radio(key="e3_modus").value == "fester Wert k"
    texte = _texte(at, "success") + _texte(at, "info") + _texte(at, "warning")
    assert any(t.startswith("Bei k = 8 (unerfüllbar), n = 25, 10 Graphen:") for t in texte)


def test_live_messreihe_laeuft_und_zeigt_das_verdikt():
    at = _app()
    next(b for b in at.button if b.label == "Messreihe live starten").click().run(timeout=300)
    assert not at.exception
    assert any("Live gemessen, nicht vorgerechnet" in c.value for c in at.caption)


@pytest.mark.parametrize("name", list(C.PRESETS))
def test_jedes_preset_zeigt_eine_zelle_und_kein_verdikt_ohne_zaehlung(name):
    at = _app()
    at.sidebar.button(key=f"preset_{name}").click().run()
    assert not at.exception
    texte = _texte(at, "success") + _texte(at, "info") + _texte(at, "warning")
    assert any("von 10 Graphen hat der Totalizer weniger Konflikte" in t for t in texte), name


def test_permalink_uebernimmt_die_einstellungen():
    at = _app(e3n="60", modus="Optimum − 1", kod="Totalizer")
    assert at.select_slider(key="e3_n").value == 60 and at.radio(key="e3_modus").value == "Optimum − 1" and at.radio(key="e1_verfahren").value == "Totalizer"
