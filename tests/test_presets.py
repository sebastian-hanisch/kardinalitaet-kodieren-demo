"""Presets: Vollständigkeit, gültige Werte, Standard-Preset = Voreinstellungen; jedes Preset durchläuft die Verdikte der Experimente (DEMO-PLAYBOOK §11a Punkt 7)."""

import pytest

import kkd_algorithm as A
import kkd_constants as C
import kkd_evaluation as E
import kkd_presets as P


def test_jedes_preset_hat_hilfetext_und_nur_bekannte_schluessel():
    assert set(C.PRESETS) == set(C.PRESET_HELP)
    for name, preset in C.PRESETS.items():
        assert set(preset) <= set(P.SETTING_SPECS) | {"e1_belegung"}, name
        assert C.PRESET_HELP[name]


def test_presetwerte_liegen_in_den_reglergrenzen_und_optionen():
    for name, preset in C.PRESETS.items():
        for key, wert in preset.items():
            if key == "e1_belegung":
                assert all(1 <= i <= preset.get("e1_n", C.DEFAULT_E1_N) and w in C.E1_BELEGUNG for i, w in wert.items()), name
                continue
            spec = P.SETTING_SPECS[key]
            assert wert in spec.options if spec.options else spec.lo <= wert <= spec.hi, (name, key)


def test_standard_preset_ist_das_erste_und_gleich_den_voreinstellungen():
    erstes = C.PRESETS[next(iter(C.PRESETS))]
    assert all(erstes.get(key, spec.default) == spec.default for key, spec in P.SETTING_SPECS.items())
    for name, preset in list(C.PRESETS.items())[1:]:
        assert any(preset.get(key, spec.default) != spec.default for key, spec in P.SETTING_SPECS.items()), f"{name} entspricht den Voreinstellungen"


def test_setting_specs_und_preset_keys_decken_sich():
    assert set(P.PRESET_KEYS.values()) == set(P.SETTING_SPECS)


def test_handbeispiel_preset_setzt_x1_x2_und_den_sinz_zaehler():
    p = C.PRESETS["Handbeispiel"]
    assert (p["e1_n"], p["e1_k"], p["e1_verfahren"], p["e1_belegung"]) == (4, 2, "Sinz-Zähler", {1: "wahr", 2: "wahr"})


def test_permalink_rastet_auf_erlaubte_werte_ein():
    spec = P.SETTING_SPECS
    assert P.einrasten(spec["e3_n"], "47") == 50 and P.einrasten(spec["e3_n"], "x") is None
    assert P.einrasten(spec["e3_grad"], "3.4") == 3.5 and P.einrasten(spec["e3_modus"], "Optimum − 1") == "Optimum − 1" and P.einrasten(spec["e3_modus"], "irgendwas") is None
    assert P.einrasten(spec["e1_n"], "99") == 8 and P.einrasten(spec["e1_n"], "-5") == 3 and P.einrasten(spec["seed"], "-1") == 0
    assert P.einrasten(spec["e1_verfahren"], "Totalizer") == "Totalizer" and P.einrasten(spec["budget"], "60000") == 50000


@pytest.mark.parametrize("name", list(C.PRESETS))
def test_jedes_preset_durchlaeuft_jedes_verdikt(name):
    preset = C.PRESETS[name]
    wert = lambda key: preset.get(key, P.SETTING_SPECS[key].default)
    # Experiment 1: Kodierung und Propagation (kein Konflikt-Text nötig, aber die Kodierung muss sich bauen lassen)
    n1, k1 = wert("e1_n"), wert("e1_k")
    kod = A.kodierung(n1, k1, C.LABEL_VERFAHREN[wert("e1_verfahren")])
    feste = {i: w == "wahr" for i, w in preset.get("e1_belegung", {}).items() if w != "offen"}
    assert A.propagiere(kod.klauseln, kod.n_gesamt, feste).konflikt is None
    # Experiment 2: Größenverhältnis am Punkt
    kl = {v: A.klauselzahl(v, wert("e2_n"), wert("e2_k")) for v in C.VERFAHREN}
    hv = {v: A.hilfsvariablen(v, wert("e2_n"), wert("e2_k")) for v in C.VERFAHREN}
    assert E.verdict_groesse(wert("e2_n"), wert("e2_k"), kl, hv)[1].startswith(f"Bei n = {wert('e2_n')}, k = {wert('e2_k')}")
    # Experiment 3: die vorgerechnete Zelle des Presets ist vorhanden und das Verdikt nennt die Zählung
    modus = wert("e3_modus")
    zelle = E.referenz_zelle(wert("e3_n"), wert("e3_grad"), modus, wert("e3_k") if modus == "fester Wert k" else None)
    assert zelle is not None, name
    kind, text = E.verdict_konflikte(zelle)
    assert "von 10 Graphen hat der Totalizer weniger Konflikte" in text and kind in ("success", "info")
