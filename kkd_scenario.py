"""Szenario: das Handbeispiel „höchstens 2 von 4“, kleine Konfliktgraphen zum Nachrechnen von Hand und die Graphen der Messreihen.

Die Graphen der Messreihen sind Zufallsgraphen mit mittlerem Grad 3 oder 3,5 (`kkd_algorithm.graph`, ganzzahliger SplitMix64, gleiche Eingabe
gleicher Graph auf jeder Plattform): n Aufträge, eine Kante verbindet zwei Aufträge mit Zeitfenster-Konflikt (derselbe Konfliktgraph wie `rampen_instanz`
der Linie). Kontrollpunkte: jede Unverträglichkeit muss an mindestens einem ihrer beiden Aufträge kontrolliert werden (Vertex Cover).
"""

import kkd_algorithm as A
import kkd_constants as C

HAND_N, HAND_K = 4, 2

# Kleine Graphen mit von Hand bekanntem Optimum
DREIECK = (3, ((0, 1), (1, 2), (0, 2)))          # Optimum 2: zwei der drei Aufträge
PFAD3 = (3, ((0, 1), (1, 2)))                    # Optimum 1: der mittlere Auftrag


def graphen(n: int, grad: float) -> list:
    """Die zehn festen Graphen einer Zelle (Seeds `GRAPH_SEEDS`)."""
    return [A.graph(n, grad, s) for s in C.GRAPH_SEEDS]


def beschreibung(n: int, grad: float) -> str:
    kanten = int(round(n * grad / 2))
    return f"{n} Aufträge, {kanten} Unverträglichkeiten (mittlerer Grad {str(grad).replace('.', ',')})"
