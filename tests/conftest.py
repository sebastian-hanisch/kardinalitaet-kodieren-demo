"""Gemeinsame Fixtures: die Mini-Instanzen, an denen jede Einheit von Hand geprüft wird (DEMO-PLAYBOOK §1b)."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import kkd_algorithm as A  # noqa: E402


@pytest.fixture
def hand():
    """Das Handbeispiel „höchstens 2 von 4“ in den drei Kodierungen."""
    return {v: A.kodierung(4, 2, v) for v in A.K.VERFAHREN}
