"""Permalink (Begrenzen/Einrasten), Presets und Zufalls-Seed-Button (Standardmuster aus dem Demo-Portfolio).

Die Regler der Seitenleiste (Zufalls-Seed, Konfliktbudget) und die Regler der Experimente im Hauptbereich stehen alle in SETTING_SPECS: ein Preset legt Werte
für beide fest, und das aktive Preset ist hervorgehoben, solange jeder dieser Regler dem Preset entspricht. Die Belegung der Eingänge in Experiment 1
(`e1_x1` … `e1_x8`) gehört nicht dazu; ein Preset setzt sie nur, ändert sie der Nutzer, bleibt die Hervorhebung.
"""

import random
from dataclasses import dataclass

import streamlit as st

import kkd_constants as C


@dataclass(frozen=True)
class SettingSpec:
    url_param: str
    caster: type
    default: object
    lo: float | None = None
    hi: float | None = None
    options: tuple = ()


SETTING_SPECS = {
    "seed": SettingSpec("seed", int, C.DEFAULT_SEED, 0, C.SEED_MAX),
    "budget": SettingSpec("budget", int, C.DEFAULT_BUDGET, options=C.BUDGET_OPTIONEN),
    "e1_n": SettingSpec("n", int, C.DEFAULT_E1_N, *C.E1_N),
    "e1_k": SettingSpec("k", int, C.DEFAULT_E1_K, *C.E1_K),
    "e1_verfahren": SettingSpec("kod", str, C.DEFAULT_E1_VERFAHREN, options=tuple(C.VERFAHREN_LABEL.values())),
    "e2_n": SettingSpec("e2n", int, C.DEFAULT_E2_N, *C.E2_N_FEST),
    "e2_k": SettingSpec("e2k", int, C.DEFAULT_E2_K, *C.E2_K_FEST),
    "e3_n": SettingSpec("e3n", int, C.DEFAULT_E3_N, options=C.E3_N),
    "e3_grad": SettingSpec("grad", float, C.DEFAULT_E3_GRAD, options=C.E3_GRAD),
    "e3_modus": SettingSpec("modus", str, C.DEFAULT_E3_MODUS, options=C.E3_MODI),
    "e3_k": SettingSpec("e3k", int, C.DEFAULT_E3_K, *C.E3_K),
}
PRESET_KEYS = {key: key for key in SETTING_SPECS}      # Schlüssel im Preset = Schlüssel des Reglers
BELEGUNG_KEY = "e1_x{}"                                # Eingang i von Experiment 1: "offen" | "wahr" | "falsch"


def init_session_state_defaults():
    for state_key, spec in SETTING_SPECS.items():
        if state_key not in st.session_state:
            st.session_state[state_key] = spec.default


def einrasten(spec: SettingSpec, roh):
    """Wert aus der Adresszeile auf einen erlaubten Wert bringen (Zahlen: begrenzen bzw. auf die nächste Option, Text: nur erlaubte Werte), sonst None."""
    try:
        wert = spec.caster(roh)
    except (ValueError, TypeError):
        return None
    if spec.options:
        if spec.caster in (int, float):
            return min(spec.options, key=lambda o: abs(o - wert))
        return wert if wert in spec.options else None
    return max(spec.lo, min(spec.hi, wert))


def load_permalink_settings():
    """Einmal je Sitzung: Werte aus der Adresszeile übernehmen, auf erlaubte Werte begrenzt."""
    if "permalink_loaded" in st.session_state:
        return
    qp = st.query_params
    for state_key, spec in SETTING_SPECS.items():
        if spec.url_param in qp:
            wert = einrasten(spec, qp[spec.url_param])
            if wert is not None:
                st.session_state[state_key] = wert
    st.session_state["permalink_loaded"] = True


def sync_query_params(values):
    """`values`: {state_key: aktueller Wert}; die Adresszeile spiegelt die Konfiguration."""
    try:
        for state_key, value in values.items():
            st.query_params[SETTING_SPECS[state_key].url_param] = str(value)
    except Exception:
        pass


def apply_preset(name):
    preset = C.PRESETS[name]
    for key, spec in SETTING_SPECS.items():
        st.session_state[key] = preset.get(key, spec.default)
    # Belegung der Eingänge von Experiment 1: nur die Eingänge 1..n werden gesetzt (nur diese werden gezeichnet)
    belegung = preset.get("e1_belegung", {})
    for i in range(1, st.session_state["e1_n"] + 1):
        st.session_state[BELEGUNG_KEY.format(i)] = belegung.get(i, "offen")


def aktives_preset():
    """Name des Presets, dessen Werte GENAU den aktuellen Einstellungen entsprechen, sonst None.

    Zustandslos: verglichen wird jeder Regler aus SETTING_SPECS mit dem Session State (ein Preset ohne Eintrag für einen Regler meint dessen Standardwert)."""
    for name, preset in C.PRESETS.items():
        if all(st.session_state.get(key, spec.default) == preset.get(key, spec.default) for key, spec in SETTING_SPECS.items()):
            return name
    return None


def sidebar_presets():
    """Schnellstart oben in der Seitenleiste; das aktive Preset ist hervorgehoben (`type="primary"`)."""
    if not C.PRESETS:
        return
    st.header("🎯 Schnellstart")
    st.caption("Ein Beispielszenario laden:")
    aktiv = aktives_preset()
    for name in C.PRESETS:
        st.button(
            name, width="stretch", on_click=apply_preset, args=(name,), help=C.PRESET_HELP.get(name, ""), key=f"preset_{name}",
            type="primary" if aktiv == name else "secondary",
        )


def randomize_seed():
    st.session_state["seed"] = random.randint(0, C.SEED_MAX)
