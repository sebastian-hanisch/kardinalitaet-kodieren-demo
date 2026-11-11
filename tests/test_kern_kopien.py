"""Die kopierten Kern-Module (`kkd_rng`, `kkd_instanzen`, `kkd_kodierung`, `kkd_cdcl`): wörtliche Kopie, Regressionswerte, Einheiten mit Handrechnung.

Der Hash-Test (Kern-Version im Modulkopf gegen den Text der Kopie mit rückübersetzten Importen) läuft immer; der Vergleich mit dem Kern selbst nur, solange der Ordner
`sat-cp-planung/kern` neben dem Repo liegt. Die Regressionswerte stehen unabhängig davon im Test."""

import hashlib
import re
from math import comb
from pathlib import Path

import pytest

import kkd_instanzen as I
import kkd_kodierung as K
from kkd_cdcl import Loeser, luby, solve
from kkd_rng import SplitMix64

ROOT = Path(__file__).resolve().parent.parent
KERN = ROOT.parent / "sat-cp-planung" / "kern"
MODULE = ("rng", "instanzen", "kodierung", "cdcl")
VERSION = {"rng": "5d5d8f45d0e1eddf", "instanzen": "6795de796b66fff8", "kodierung": "208571302afd04b4", "cdcl": "832b2c10dfdea62d"}
ERLAUBTE_IMPORTE = {"heapq", "itertools", "dataclasses", "typing", "math", "kkd_rng"}


def _lies(pfad: Path) -> str:
    return pfad.read_bytes().decode("utf-8").replace("\r\n", "\n")


def _kern_text(modul: str) -> tuple[str, str]:
    """(Kern-Version aus dem Kopf, Text der Kopie im Zustand des Kerns)."""
    text = _lies(ROOT / f"kkd_{modul}.py")
    kopf, zweite, rest = text.split("\n", 2)
    version = re.search(r"Kern-Version ([0-9a-f]{16})", kopf).group(1)
    assert "kkd_" in zweite
    return version, re.sub(r"^from kkd_rng import", "from rng import", rest, flags=re.M)


@pytest.mark.parametrize("modul", MODULE)
def test_kopie_gleicht_der_kern_version(modul):
    version, text = _kern_text(modul)
    assert version == VERSION[modul]
    assert hashlib.sha256(text.encode("utf-8")).hexdigest()[:16] == version


@pytest.mark.parametrize("modul", MODULE)
def test_kopie_gleicht_dem_kern_bis_auf_kopf_und_importe(modul):
    quelle = KERN / f"{modul}.py"
    if not quelle.exists():
        pytest.skip("kern/ liegt nicht neben dem Repo")
    assert _kern_text(modul)[1] == _lies(quelle)


def test_kern_version_stimmt_mit_hashes_txt():
    hashes = KERN / "HASHES.txt"
    if not hashes.exists():
        pytest.skip("kern/ liegt nicht neben dem Repo")
    eintraege = {z.split()[1]: z.split()[0] for z in hashes.read_text(encoding="utf-8").splitlines() if z.strip()}
    for modul, version in VERSION.items():
        assert eintraege[f"{modul}.py"] == version


def test_kopien_importieren_nichts_aus_dem_kern_oder_anderen_demos():
    for modul in MODULE:
        for zeile in _lies(ROOT / f"kkd_{modul}.py").splitlines():
            if zeile.startswith(("import ", "from ")):
                assert zeile.split()[1] in ERLAUBTE_IMPORTE, (modul, zeile)


# --- SplitMix64 und Instanzen -------------------------------------------------------------------------------------------------------------

def test_splitmix_bekannte_werte():
    g = SplitMix64(0)
    assert [g.next() for _ in range(3)] == [0xE220A8397B1DCDAF, 0x6E789E6AA1B965F4, 0x06C45D188009454F]
    h = SplitMix64(12345)
    assert [h.next() for _ in range(3)] == [2454886589211414944, 3778200017661327597, 2205171434679333405]


def test_zufallskanten_deterministisch_und_ohne_doppelte():
    a, b = I.zufallskanten(25, 38, 600), I.zufallskanten(25, 38, 600)
    assert a == b and len(set(a)) == 38 and all(x < y for x, y in a) and a == sorted(a)
    assert I.zufallskanten(25, 38, 601) != a
    with pytest.raises(ValueError):
        I.zufallskanten(3, 4, 0)


# --- Kodierungen des Kerns (Handwerte) -----------------------------------------------------------------------------------------------------

def test_kern_kodierungen_handbeispiel_zahlen():
    for verfahren, (kl, hv) in {"binomial": (4, 0), "sinz": (13, 6), "totalizer": (15, 7)}.items():
        pool = K.Hilfsvariablen(4)
        assert len(K.hoechstens([1, 2, 3, 4], 2, pool, verfahren)) == kl and pool.n - 4 == hv


def test_kern_formeln_n25_k5():
    assert K.klauselzahl_binomial(25, 5) == comb(25, 6) == 177100
    assert K.klauselzahl_sinz(25, 5) == 2 * 25 * 5 + 25 - 15 - 1 == 259


# --- CDCL-Einheiten -----------------------------------------------------------------------------------------------------------------------

def test_luby_folge():
    assert [luby(i) for i in range(1, 16)] == [1, 1, 2, 1, 1, 2, 4, 1, 1, 2, 1, 1, 2, 4, 8]


def test_konfliktanalyse_1uip_handrechnung():
    """c1 = (¬1 ∨ 2), c2 = (¬1 ∨ 3 ∨ 5), c3 = (¬2 ∨ 4), c4 = (¬3 ∨ ¬4). Entscheidung ¬5, dann 1: 1 → 2, 3, 4, c4 verletzt; gelernt (¬1 ∨ 5), Sprung auf Stufe 1."""
    s = Loeser(5, [(-1, 2), (-1, 3, 5), (-2, 4), (-3, -4)])
    s.entscheide(-5)
    assert s.propagiere() is None
    s.entscheide(1)
    k = s.propagiere()
    klausel, rueck, lbd = s.analysiere(k)
    assert sorted(klausel) == [-1, 5] and rueck == 1 and lbd == 2


def test_solve_kleine_antworten():
    assert solve(2, [(1,), (-1,)]).antwort is False
    assert solve(2, [(1, 2), (-1,)]).modell == {1: False, 2: True}
    assert solve(30, [(i, i + 1) for i in range(1, 30)] + [(-i, -(i + 1)) for i in range(1, 30)]).antwort is True
