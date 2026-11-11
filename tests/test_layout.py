"""Layout (DEMO-PLAYBOOK §2): fester Kopf, Schnellstart oben in der Seitenleiste, aktives Preset hervorgehoben.

Die Hervorhebung ist zustandslos (`aktives_preset` vergleicht jeden Regler aus SETTING_SPECS mit dem Preset). Die Regler der Experimente stehen im Hauptbereich,
die allgemeinen Einstellungen (Zufalls-Seed, Konfliktbudget) in der Seitenleiste; beide Gruppen stehen in SETTING_SPECS."""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

import kkd_constants as C
import kkd_presets as P

APP = str(Path(__file__).resolve().parent.parent / "app.py")
REGLER_ARTEN = ("slider", "number_input", "select_slider", "selectbox", "radio", "toggle", "checkbox", "text_input")
SEITENLEISTE = {"seed", "budget"}


def _app() -> AppTest:
    at = AppTest.from_file(APP, default_timeout=180)
    at.run()
    assert not at.exception, [str(e) for e in at.exception]
    return at


def _typen(at) -> dict:
    return {b.label: b.proto.type for b in at.sidebar.button if b.label in C.PRESETS}


def _regler(at, key):
    for bereich in (at.sidebar, at.main):
        for art in REGLER_ARTEN:
            try:
                return getattr(bereich, art)(key=key)
            except KeyError:
                continue
    raise AssertionError(f"Regler {key} nicht gefunden")


def test_presets_stehen_in_der_seitenleiste_und_nicht_im_hauptbereich():
    at = _app()
    assert [b.label for b in at.sidebar.button][: len(C.PRESETS)] == list(C.PRESETS)
    assert not [b for b in at.main.button if b.label in C.PRESETS]


def test_allgemeine_einstellungen_stehen_in_der_seitenleiste_experimentregler_im_hauptbereich():
    at = _app()
    seiten = {w.key for art in REGLER_ARTEN for w in getattr(at.sidebar, art) if w.key}
    haupt = {w.key for art in REGLER_ARTEN for w in getattr(at.main, art) if w.key}
    assert SEITENLEISTE <= seiten and not (SEITENLEISTE & haupt)
    assert {"e1_n", "e1_k", "e1_verfahren", "e2_n", "e2_k", "e3_n", "e3_grad", "e3_modus", "e3_k"} <= haupt


def test_titel_steht_im_festen_kopf():
    at = _app()
    assert "st-key-kopf" in " ".join(h.proto.body for h in at.get("html"))
    assert at.title[0].value


def test_beim_start_ist_genau_das_standard_preset_hervorgehoben():
    assert [n for n, t in _typen(_app()).items() if t == "primary"] == [next(iter(C.PRESETS))]


@pytest.mark.parametrize("name", list(C.PRESETS))
def test_angeklicktes_preset_ist_hervorgehoben_und_bleibt_es_im_naechsten_lauf(name):
    at = _app()
    at.sidebar.button(key=f"preset_{name}").click().run()
    assert not at.exception
    assert [n for n, t in _typen(at).items() if t == "primary"] == [name]
    at.run()
    assert [n for n, t in _typen(at).items() if t == "primary"] == [name]


def test_jeder_regler_der_seitenleiste_steht_in_setting_specs():
    at = _app()
    schluessel = {w.key for art in REGLER_ARTEN for w in getattr(at.sidebar, art) if w.key}
    fehlt = schluessel - set(P.SETTING_SPECS)
    assert not fehlt, f"Regler {sorted(fehlt)} fehlen in SETTING_SPECS: ihre Änderung hebt das aktive Preset nicht auf"


@pytest.mark.parametrize("state_key", list(P.SETTING_SPECS))
def test_jede_aenderung_eines_reglers_hebt_die_hervorhebung_auf(state_key):
    at = _app()
    spec = P.SETTING_SPECS[state_key]
    regler = _regler(at, state_key)
    if spec.options:
        regler.set_value(next(o for o in spec.options if o != regler.value))
    else:
        regler.set_value(spec.hi if regler.value != spec.hi else spec.lo)
    at.run()
    assert not at.exception, [str(e) for e in at.exception]
    assert "primary" not in _typen(at).values(), state_key
    name = next(iter(C.PRESETS))
    at.sidebar.button(key=f"preset_{name}").click().run()
    assert _typen(at)[name] == "primary"
