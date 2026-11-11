# Kardinalität kodieren – Streamlit-Demo

<!-- TODO nach dem Deploy: direkt hierher den Live-Link setzen (Leerzeile davor und danach):
**[→ Demo live ausprobieren](https://sebastianhanisch-kardinalitaet-kodieren-demo.streamlit.app/)** -->

Demo der Linie **SAT und Constraint Programming** in der „Konzepte“-Reihe für die Website „Sebastian Hanisch – Operations Research und Machine Learning“. Sie baut auf dem Konfliktlernen auf und beantwortet die Frage, die dort offen bleibt: Ein Löser kennt nur Klauseln, eine **Zählbedingung** („höchstens k von n“) ist keine kurze Klausel. Die Demo zeigt an einer Regel mit vier Eingängen von Hand, wie **drei Übersetzungen** (binomial, Sinz-Zähler, Totalizer) dieselbe Regel in Klauseln schreiben, wie ihre **Größe** wächst und was sie dem Löser an **Konflikten** kosten. Vehikel sind **Kontrollpunkte im Konfliktgraphen**: Aufträge mit Unverträglichkeiten (derselbe Konfliktgraph wie die Rampen-Instanz der Linie), jede Unverträglichkeit muss an mindestens einem ihrer beiden Aufträge kontrolliert werden, höchstens k Kontrollen (Vertex Cover höchstens k).

## Warum dieses Problem

Die naheliegende Übersetzung verbietet jede Auswahl von k + 1 Eingängen einzeln: C(n, k + 1) Klauseln, bei n = 25 und k = 5 sind es **177.100**. Der Sinz-Zähler schreibt dieselbe Regel in **259** Klauseln mit 120 Hilfsvariablen, der Totalizer in **279** mit 85. Alle drei erlauben genau dieselben Belegungen der Eingänge, und die Einheitspropagation schließt aus allen dreien dasselbe (ausgezählt an 81, 729 und 5.000 Teilbelegungen). Der Unterschied liegt in der **Größe** und im **Suchverlauf**: Auf den gemessenen Graphen braucht der Sinz-Zähler am Optimum ab n = 50 im Median mehr Konflikte als der Totalizer (2,2- bis 4,3-fach in den gemessenen Zellen; der Totalizer hat dabei in 6 bis 9 von 10 Graphen weniger), darunter hängt die Richtung von den Graphen ab, und knapp unter dem Optimum ist der Unterschied klein.

## Modell

- **Zählregel.** „Höchstens k von n Eingängen sind wahr“, in drei Kodierungen (Kern-Kopie `kkd_kodierung.py`): **binomial** (je k + 1 Eingänge ein verneinter, C(n, k + 1) Klauseln, keine Hilfsvariable), **Sinz-Zähler** (sequentieller Zähler, 2nk + n − 3k − 1 Klauseln und (n − 1)k Hilfsvariablen für 1 ≤ k < n) und **Totalizer** (Addierbaum in Einerdarstellung, bei k + 1 Ausgängen je Knoten abgeschnitten, nur die Richtung Eingang → Ausgang; Klauseln und Hilfsvariablen per Rekursion über den Baum). „Mindestens k“ ist „höchstens n − k“ der verneinten Eingänge (Kern, nicht in der App).
- **Frage der Messreihen.** Kontrollpunkte im Konfliktgraphen: ein Zufallsgraph mit n Aufträgen und mittlerem Grad 3 oder 3,5 (`kkd_algorithm.graph`, ganzzahliger SplitMix64, auf jeder Plattform derselbe Graph); Klauseln (x_a ∨ x_b) für jede Kante plus die Zählregel über alle Aufträge. k ist das **Optimum** des Graphen (erfüllbar), das **Optimum − 1** (unerfüllbar) oder ein **fester Wert**. Das Optimum je Graph ist eingefroren (`kkd_optima.json`, bestimmt mit OR-Tools CP-SAT durch `tools/optima.py`).
- **Löser.** CDCL der Linie (Kern-Kopie `kkd_cdcl.py`): 1-UIP, Aktivität (VSIDS-Variante), Phasenspeicher, Luby-Neustarts (Einheit 32), ohne Löschen. Aufwand wird in **Konflikten** gezählt, nie in Sekunden. Ein Lauf, der das Konfliktbudget erreicht, antwortet „unbekannt“, nie „unerfüllbar“, und zählt mit dem Budget.
- **Messreihen.** 10 feste Graphen je Zelle (Zufalls-Seeds 600 bis 609 des Graphenerzeugers), ein Lauf je Graph und Kodierung, Median, Minimum und Maximum der Konflikte und die **Zählung** über die Graphen („in k von 10 Graphen weniger Konflikte beim Totalizer“). Die binomiale Kodierung wird nur bis 400.000 Klauseln gebaut, darüber steht nur die Formel.
- Mathematik und Symboltabelle: Expander **📐 Mathematische Formulierung** in der App.

## Methodik

| Baustein | Datei | Anmerkung |
|---|---|---|
| CDCL | `kkd_cdcl.py` | **wörtliche Kopie** des Kern-Moduls `cdcl.py` der Linie (Kern-Version 832b2c10dfdea62d); nur der Import ist auf `kkd_rng` umgestellt (`tests/test_kern_kopien.py`) |
| SplitMix64 | `kkd_rng.py` | Kopie von `rng.py` (5d5d8f45d0e1eddf); Regressionstest auf veröffentlichte Referenzwerte |
| Instanzerzeuger (hier: `zufallskanten`) | `kkd_instanzen.py` | Kopie von `instanzen.py` (6795de796b66fff8) |
| Kodierungen binomial, Sinz, Totalizer | `kkd_kodierung.py` | Kopie von `kodierung.py` (208571302afd04b4); der Kern-Hash-Test läuft in jeder Umgebung, der Vergleich mit dem Kern nur neben dem Ordner `sat-cp-planung/kern` |
| Namen und Gruppen der Klauseln, Formeln, Einheitspropagation, Semantikprüfung, Vollständigkeit, Kontrollpunkte, Löserlauf | `kkd_algorithm.py` | eigene Einheiten: `kodierung`, `klauselzahl`, `hilfsvariablen`, `Propagator`, `propagiere`, `erfuellbar`, `semantik_pruefen`, `vollstaendigkeit`, `kontrollpunkte`, `optimum`, `messe_lauf` |
| Handbeispiel, kleine Graphen, Beschreibung | `kkd_scenario.py` | Dreieck (Optimum 2) und Pfad mit drei Knoten (Optimum 1) zum Nachrechnen von Hand |
| Messreihen, Kennzahlen, Verdikte | `kkd_evaluation.py` | Verdikte sind reine Funktionen; jede Zahl im Text stammt aus den Kennzahlen |
| Vorgerechnete Messreihen | `kkd_messungen.json` | geschrieben von `tools/messungen.py` (dieselben Funktionen wie die Live-Messreihe), Budget 300.000 Konflikte |
| Eingefrorene Optima | `kkd_optima.json` | geschrieben von `tools/optima.py` (OR-Tools CP-SAT); in der App nie benutzt |

Experimente in der App: **Eine Regel von Hand** (n = 3 bis 8, k = 0 bis 7, drei Kodierungen; alle Klauseln mit lesbaren Namen und Gruppen, Eingänge auf wahr, falsch oder offen setzen, Einheitspropagation Schritt für Schritt mit auslösender Klausel, Konflikt rot; Aufzählung aller 2^n Eingaben), **Wie wächst die Kodierung** (Klauseln über n und über k, Formel als Linie, gebaute Zahlen als Kreise), **Dieselbe Frage, drei Kodierungen** (vorgerechnet, dazu live), **Ist die Einheitspropagation vollständig** (alle 729 Teilbelegungen bei n = 6, k = 2 und 5.000 Zufallsteilbelegungen bei n = 10, k = 3). Die großen Messreihen sind **vorgerechnet, nicht live**; im Experiment 3 rechnet ein Knopf dieselbe Messreihe live nach (Konfliktbudget in der Seitenleiste).

## Befunde (gemessen, keine Behauptungen)

Alle Zahlen dieser Tabelle stehen in `tests/test_claims.py` (Messungen: `kkd_messungen.json` mit Budget 300.000 Konflikten, Skript `tools/messungen.py`; Optima: `kkd_optima.json`). Zufallsgraphen mit mittlerem Grad 3 oder 3,5, **10 feste Graphen** je Zelle (Seeds 600 bis 609), ein Lauf je Graph und Kodierung. Konflikte als Median (Maximum). **Kein Lauf erreichte das Budget, und alle 480 Antworten von Sinz-Zähler und Totalizer (24 Zellen mit je 10 Graphen) stimmen mit dem Optimum überein** (erfüllbar genau bei k ≥ Optimum; jedes Modell wurde gegen die Kantenklauseln und die Zählregel geprüft; dazu die 10 Antworten der binomialen Kodierung bei n = 25, k = 5).

| Frage | Befund |
|---|---|
| **Größe, n = 25, k = 5** (nur Zählerklauseln, ohne Kantenklauseln) | binomial 177.100 = C(25, 6), Sinz-Zähler 259 Klauseln mit 120 Hilfsvariablen, Totalizer 279 mit 85. Die binomiale Kodierung ist 684-mal so groß wie der Sinz-Zähler und 635-mal so groß wie der Totalizer (`test_claim_groesse_n25_k5`). Mit den 38 Kantenklauseln des Graphen (Seed 600): 177.138 / 297 / 317. |
| **Handbeispiel „höchstens 2 von 4“** | 4 / 13 / 15 Klauseln, 0 / 6 / 7 Hilfsvariablen; für alle 16 Belegungen der Eingänge hat jede Kodierung genau dann eine Fortsetzung auf die Hilfsvariablen, wenn höchstens 2 wahr sind (0 Abweichungen); x1 = x2 = wahr erzwingt x3 = x4 = falsch (`tests/test_algorithm.py`, von Hand nachgerechnet). |
| **Einheitspropagation vollständig?** | Bei n = 4, k = 2: alle 81 Teilbelegungen; bei n = 6, k = 2: alle 729; bei n = 10, k = 3: 5.000 Zufallsteilbelegungen (Zufalls-Seed 35). In allen drei Kodierungen ist **keine** erzwungene Belegung und **keine** Verletzung übersehen und kein falscher Schluss gezogen worden: n = 6, k = 2: 233 Verletzungen und 480 erzwungene Eingänge, alle gefunden; n = 10, k = 3: 2.155 Verletzungen und 4.642 erzwungene Eingänge, alle gefunden. Das gilt für diese Zellen und diese Zufallsteilbelegungen; die Zahlen 2.155 und 4.642 gehören zum Zufalls-Seed 35, „keine übersehen“ gilt auch für die Zufalls-Seeds 0 bis 4 (`test_claim_vollstaendigkeit`). |
| **Klein und gleich: n = 25, k = 5 (fester Wert, unerfüllbar)** | Konflikte: binomial 8,5 (10), Sinz-Zähler 10 (14), Totalizer 10 (11); bei 177.138 gegen 297 und 317 Klauseln einschließlich der Kantenklauseln. Die binomiale Kodierung braucht hier nicht mehr Konflikte, aber die Konfliktzahl sagt nichts über den Speicher (`test_claim_klein_und_gleich`). Bei k = 8 (die binomiale Kodierung ist mit 2.043.013 Klauseln über der Grenze nicht gebaut): Sinz-Zähler 25 (29), Totalizer 22,5 (33). |
| **Am Optimum (erfüllbar)** | Verhältnis der Mediane Sinz-Zähler zu Totalizer: **n = 25 bis 40: keine einheitliche Richtung** (Grad 3 / 3,5: n = 25: 0,7 / 0,8, n = 30: 0,9 / 1,3, n = 40: 1,9 / 0,6), **n = 50: 2,5 / 2,5** (Grad 3 / 3,5), **n = 60: 4,3 / 2,2**. In den vier Zellen mit n ≥ 50 braucht der Sinz-Zähler im Median mehr Konflikte; der Totalizer hat dabei in 6 / 6 (n = 50) und 9 / 7 (n = 60) von 10 Graphen weniger (Grad 3 / 3,5), gegen 4 / 4 und 1 / 3 mit mehr (`test_claim_am_optimum`). Die Richtung ist je Zelle nur in einer von vier Zellen statistisch sichtbar (Vorzeichentest: 6 gegen 4 bei n = 50, beide Grade, p = 0,75; n = 60, Grad 3,5: 7 gegen 3, p = 0,34; nur n = 60, Grad 3: 9 gegen 1, p = 0,02); der Median-Faktor hängt stark von wenigen Graphen mit langer Suche ab. |
| **Knapp unter dem Optimum (unerfüllbar)** | Verhältnis der Mediane Sinz-Zähler zu Totalizer bei k = Optimum − 1: **0,9 bis 1,2** in allen 10 Zellen mit n = 25 bis 60 (n = 25 bis 50: 0,9 bis 1,1, n = 60: 1,2 / 1,2); Richtung nicht einheitlich. Bei n = 60 braucht der Sinz-Zähler 8.129,5 (14.937) gegen 6.507,5 (10.306) Konflikte (Grad 3) (`test_claim_knapp_unter_dem_optimum`). |
| **Deutlich unter dem Optimum (unerfüllbar), n = 60, Grad 3** | k = 22: Sinz-Zähler 837,5 (1.067), Totalizer 507 (739), Verhältnis 1,7, der Totalizer hat in **10 von 10** Graphen weniger Konflikte; k = 26: 3.272 (4.493) gegen 2.274 (2.727), Verhältnis 1,4, in 9 von 10 Graphen weniger (`test_claim_deutlich_unter_dem_optimum`). |
| **Größe der Zählerkodierungen im Graphen** | Median der Hilfsvariablen am Optimum, Grad 3: Sinz-Zähler gegenüber Totalizer 288 / 106 (n = 25), 741 / 196 (n = 40), 1.711 / 326 (n = 60); Median der Klauseln 626 / 457, 1.562 / 1.057, 3.542 / 2.217 (einschließlich Kantenklauseln) (`test_claim_groesse_im_graphen`). |

Die Zählung je Graph steht neben jedem Verhältnis, weil der Median allein täuscht: bei n = 50 und Grad 3 am Optimum ist das Verhältnis 2,5, der Totalizer hat aber nur in 6 von 10 Graphen weniger Konflikte. Die vollständige Tabelle aller 24 vorgerechneten Zellen (Median und Maximum, Zählung, Klauseln und Hilfsvariablen) steht in `tests/test_claims.py`; die App zeigt je eine Zelle.

### Stabilität (Gegenprobe, nicht Teil der Tests)

Die Gegenprobe mit **anderen festen Graphen** (`tools/gegenprobe.py`, Zufalls-Seeds 700 bis 709, Grad 3, sonst gleiche Verfahren und Budget; die Optima je Graph rechnet das Skript mit OR-Tools) ergab, jeweils Median (Maximum) der Konflikte Sinz-Zähler / Totalizer und die Zählung „Totalizer weniger / gleich / mehr“:

| k | n = 25 | n = 40 | n = 50 |
|---|---|---|---|
| Optimum | 24,5 (150) / 11 (178), Verhältnis 2,2; 5 / 3 / 2 | 412,5 (754) / 367 (1.340), Verhältnis 1,1; 2 / 0 / 8 | 1.156 (2.926) / 533 (2.078), Verhältnis 2,2; 5 / 1 / 4 |
| Optimum − 1 | – | 578 (1.094) / 639 (1.186), Verhältnis 0,9; 3 / 0 / 7 | 1.651,5 (3.183) / 1.578,5 (2.872), Verhältnis 1,05; 7 / 0 / 3 |

Am Optimum dreht sich die Richtung bei **n = 25** gegenüber der Referenzmenge um (Sinz-Zähler 2,2-mal so viele statt 0,7-mal so viele Konflikte); bei **n = 40** ist das Verhältnis 1,1 statt 1,9; bei **n = 50** stimmt es mit der Referenz überein (2,2 statt 2,5). Knapp unter dem Optimum bleibt es bei „kaum Unterschied“ (0,9 und 1,05). Die Aussage „ab n = 50 braucht der Sinz-Zähler am Optimum mehr Konflikte“ hat sich für n = 50 in beiden Graphenmengen im Median gezeigt (Verhältnis 2,5 und 2,2; Zählung 6 : 4 und 5 : 4 bei einem Gleichstand); für n = 60 gibt es nur die erste Graphenmenge. Die Richtung bei n ≤ 40 ist eine Messung je Graphenmenge und kein Befund.

## Ehrliche Grenzen

- **Eine Graphfamilie, ein Löser.** Zufallsgraphen mit mittlerem Grad 3 und 3,5 (Vertex Cover höchstens k), zehn Graphen je Zelle, ein Python-CDCL mit Aktivität, Phasenspeicher und Luby-Neustarts. Die Rangfolge Sinz-Zähler gegen Totalizer kann sich bei anderen Familien, anderen Lösern oder anderen Löserbausteinen (Neustarts, Löschen, Vorverarbeitung) ändern; sie ist hier nicht geprüft.
- **Der Totalizer ist nach der Beschreibung bei Sinz gebaut**, das Original (Bailleux und Boufkhad, CP 2003) ist nicht gelesen. „Der Totalizer braucht ab n = 50 am Optimum weniger Konflikte als der Sinz-Zähler“ ist eine **eigene Messung** an dieser Familie, keine Aussage aus der Literatur. Die Ursache ist nicht untersucht; eine Deutung (der Totalizer hat bei gleichem k weniger Hilfsvariablen: 326 gegen 1.711 bei n = 60 am Optimum, Grad 3) ist nicht gemessen.
- **Median allein täuscht.** Mit zehn Graphen je Zelle schwankt das Verhältnis der Mediane stark (siehe Stabilität); die App und diese README nennen deshalb die Zählung je Graph. Mehrere Zellen liegen im Verhältnis zwischen 0,9 und 1,2: dort ist keine Richtung belegt.
- **Dieselbe Antwort, andere Größe** gilt für die gemessenen Zellen (Antworten gegen das Optimum, Modelle geprüft); die Konfliktzahl sagt nichts über den Speicher und nichts über die Zeit je Konflikt.
- **Die Vollständigkeit der Einheitspropagation** ist nur für „höchstens 2 von 4“ (81 Teilbelegungen), „höchstens 2 von 6“ (729) und „höchstens 3 von 10“ (5.000 Zufallsteilbelegungen) ausgezählt; darüber hinaus keine Aussage. Sinz belegt die Verletzungserkennung für den Sinz-Zähler; „so stark wie die Regel selbst“ ist hier eine Aufzählung, kein Beweis.
- **Binomial nur bis 400.000 Klauseln.** Bei größerem n und k zeigt die App nur die Formel C(n, k + 1); in den Messreihen ist die binomiale Kodierung deshalb nur bei n = 25, k = 5 gebaut.
- **Python-CDCL, lesbar statt schnell.** Live laufen die Messreihen bis n = 60 (je nach Einstellung einige Sekunden bis wenige Minuten); größere Aufgaben sind nicht gemessen.
- **Konflikte sind keine Laufzeit.** Die Zeit je Konflikt hängt von der Formelgröße ab (die binomiale Kodierung braucht bei n = 25, k = 5 bei gleicher Konfliktzahl hundertmal so große Datenstrukturen); sie ist nicht gemessen.

## Befunde und Korrekturen gegenüber dem Plan

- **Neue Graphen, neue Zahlen.** Der Plan nennt Werte der Vormessung mit Python-`random`; die Demo misst mit SplitMix64 neu, die Zahlen des Plans gelten als überholt. Plan: „am Optimum braucht der Sinz-Zähler 1,3- bis 2,2-mal so viele Konflikte wie der Totalizer“ (Vormessung n = 40, 60, 80). Hier reproduziert sich das **nicht für alle Größen**: bei n = 25 bis 40 gibt es keine einheitliche Richtung (0,6 bis 1,9; die Gegenprobe dreht n = 25 um), ab n = 50 gibt es in den Messreihen und (für n = 50) in der Gegenprobe den Vorsprung des Totalizers (2,2- bis 4,3-fach; der Plan nannte n = 60: 2,2-fach, hier 4,3 bei Grad 3 und 2,2 bei Grad 3,5). Die Kernbotschaft „die Übersetzung entscheidet über die Zahl der Konflikte“ gilt in den Messungen für größere Aufgaben (n = 50 bis 60), am Optimum am deutlichsten (2,2- bis 4,3-fach), unter dem Optimum schwächer (1,2- bis 1,7-fach bei n = 60); bei n ≤ 40 ist die Richtung gemischt.
- **Knapp unter dem Optimum.** Plan: „nur 1,05- bis 1,13-fach“. Hier 0,9 bis 1,2 in 10 Zellen: kleiner Unterschied, aber in beide Richtungen.
- **Deutlich unter dem Optimum.** Plan: 1,5- bis 1,7-fach (n = 60: 914,5 gegen 542 bei k = 22). Hier n = 60, k = 22: 837,5 gegen 507 (1,7), k = 26: 3.272 gegen 2.274 (1,4); die Zelle n = 100, k = 40 des Plans fehlt (Rechenzeit des Python-Lösers, kein Optimum eingefroren), ebenso n = 28, k = 6 (das Raster hat n = 25, 30, 40, 50, 60).
- **„In 11 von 12 Zellen liegt der Totalizer-Median höchstens beim Sinz-Median“** (Plan) gilt hier für 15 der 24 vorgerechneten Zellen (`test_claim_totalizer_median_hoechstens_sinz_median`).
- **Klein und gleich.** Plan: binomial 9, Sinz 10, Totalizer 9,5; hier 8,5, 10 und 10 (n = 25, k = 5, 10 neue Graphen). Die Aussage „gleich viele Konflikte, 684-mal größere Formel“ bleibt.
- **Kern-Wünsche nicht an den Kern gegeben.** Namen der Hilfsvariablen, Gruppen je Klausel und `klauselzahl_totalizer` fehlen im Kern; die Demo leistet sie in `kkd_algorithm.py` selbst (Namen und Gruppen aus der Rekursion nachgebaut und gegen die Kern-Kodierung getestet), die Kern-Kopie bleibt wörtlich. Im Kern fehlt weiterhin eine Totalizer-Formel.
- **Totalizer-Quelle nicht beschafft.** Entscheidung Z3 empfahl, das Original zu suchen; der Bauauftrag sagt, nach Sinz zu zitieren. Es bleibt bei „nach der Beschreibung bei Sinz“.
- **Größe n = 80 entfällt.** Der Plan misst n = 40, 60 und 80 (am Optimum auch n = 80: 8.603,5 gegen 4.676,5 in der Vormessung). Hier sind zwei Läufe für n = 80 (Grad 3 und 3,5, Optimum) nach über 30 Minuten Rechenzeit je Zelle im Python-Löser abgebrochen worden; es gibt keine Zahl für n = 80, das Raster endet bei n = 60. Die Optima-Datei enthält deshalb nur n = 25 bis 60.
- **Experiment 3.** Live und vorgerechnet bis n = 60. Der Regler „k“ der Messreihe ist ein Regler: Bewegen wählt den Modus „fester Wert k“.
- **Schritte der Einheitspropagation.** Die App zählt die Schlüsse in der Reihenfolge ihrer eigenen Warteschlange; die Zahl bis zum Konflikt hängt von dieser Reihenfolge ab (Handbeispiel x1 = x2 = x3 = wahr: bis zum Konflikt 0 / 5 / 4 Schlüsse bei binomial / Sinz-Zähler / Totalizer gegenüber 0 / 6 / 6 bei der Fixpunktschleife des Handbeispiel-Skripts; `test_claim_schluesse_bis_zum_konflikt`). Der Fixpunkt ohne Konflikt (2 / 8 / 9 Schlüsse bei x1 = x2 = wahr) ist von der Reihenfolge unabhängig.

## Verifikation

- **Kern:** jede Einheit gegen Handrechnung (`tests/test_algorithm.py`): Handbeispiel (Klauseln im Wortlaut, Zahlen, Namen, Gruppen), Formeln, Randfälle (k = 0, k ≥ n, n = 1), Einheitspropagation (Fixpunkt 2 / 8 / 9 Schlüsse, Konflikt, Wiederverwendung), Dreieck und Pfad. Die kopierten Kern-Module: Kern-Hash (in jeder Umgebung), Vergleich mit dem Kern (neben `sat-cp-planung/kern`), Regression und Einheiten (`tests/test_kern_kopien.py`).
- **Orakel** (`tests/test_oracle_kardinalitaet_kodieren.py`): Semantik aller drei Kodierungen gegen die **Aufzählung aller Hilfsvariablen-Belegungen** (n bis 6) und gegen **OR-Tools CP-SAT** (n bis 6); `Propagator` gegen eine **naive Fixpunktschleife** auf allen Teilbelegungen (n bis 6); die Folgerungen der Regel (`erwartung`) gegen die **Aufzählung aller Vervollständigungen** (n bis 6, alle k); Klauselzahl des Sinz-Zählers 2nk + n − 3k − 1 für alle 2 ≤ k < n ≤ 30, (n − 1)k Hilfsvariablen, C(n, k + 1) und die Totalizer-Rekursion gegen den Aufbau; **Antwort des Lösers gegen CP-SAT** (`AddBoolOr` und `Sum ≤ k`) auf 30 Zufallsgraphen für alle drei Kodierungen bei Optimum und Optimum − 1, jedes Modell geprüft; Optimum gegen Aufzählung und CP-SAT; die 100 eingefrorenen Optima gegen CP-SAT (Optimum lösbar, Optimum − 1 nicht); „mindestens k“ und „genau k“ gegen Aufzählung; Umbenennen der Aufträge ändert die Antwort nie. Der Scratch-Lauf mit 200 Zufallsgraphen steht nicht im Repo.
- **Randfälle** (`tests/test_edge_cases.py`): n = 1, n = 2, k = 0, Grenzen inklusive, Graph ohne Kanten, vollständiger Graph, **Konfliktbudget erreicht** (Antwort „unbekannt“ wird nie als unerfüllbar gelesen, die Abbrüche zählen mit dem Budget und werden im Verdikt genannt), binomiale Kodierung über der Grenze.
- **Zweige** (`tests/test_zweige.py`): keine Nullspalte, Sinz-Zähler und Totalizer weichen in jeder Zelle ab, Modi unterscheiden sich, alle Antworten stimmen mit der Erwartung überein.
- **Verdikte** als reine Funktionen, jede Schwelle (Verhältnis 1,2 inklusive, binomial das Zehnfache) und jede Zahl im Text an handgesetzten Zellen (`tests/test_verdicts.py`); jedes Preset durchläuft jedes Verdikt (`tests/test_presets.py`). **Claims:** die Zahlen der Tabelle „Befunde“ (`tests/test_claims.py`), dazu eine Neumessung billiger Zellen gegen die JSON-Datei. Nicht in den Tests stehen die Zahlen der Gegenprobe (Skript `tools/gegenprobe.py`) und die zitierten Werte des Plans.
- **Oberfläche:** AppTest-Rauchtest (jeder Button einschließlich der Live-Messreihe, jeder Slider am Minimum und Maximum, `tests/test_app.py`), Inhaltsprüfungen (Handbeispiel, Konflikt, k ≥ n, Verdikte jedes Experiments, Permalink, `tests/test_app_inhalt.py`), Schnellstart in der Seitenleiste und Hervorhebung (`tests/test_layout.py`), Footer-Test, Laufzeit-Importe.

## Dateistruktur

| Datei | Zweck |
|---|---|
| `.github/workflows/tests.yml` | CI: Push, Pull Request, wöchentlicher Canary |
| `.gitignore` | venv, Caches, Streamlit-Secrets |
| `.streamlit/config.toml` | Streamlit-Einstellungen (keine Nutzungsstatistik) |
| `app.py` | Streamlit-App: vier Experimente, Grenzen, Mathematik |
| `requirements.txt` | Laufzeit-Bibliotheken (ungepinnt): Streamlit, Pandas, Plotly |
| `requirements-dev.txt` | Laufzeit plus pytest und OR-Tools (nur als Gegenprobe in den Tests und in `tools/`) |
| `tools/messungen.py`, `tools/optima.py`, `tools/gegenprobe.py` | Messskripte der vorgerechneten Messreihen, der Optima und der Gegenprobe |
| `kkd_algorithm.py` | Kodierungen mit Namen und Gruppen, Formeln, Einheitspropagation, Semantik, Vollständigkeit, Kontrollpunkte, Löserlauf |
| `kkd_cdcl.py`, `kkd_instanzen.py`, `kkd_kodierung.py`, `kkd_rng.py` | wörtliche Kopien der Kern-Module (Herkunft und Kern-Version im Kopf) |
| `kkd_constants.py` | Regler-Grenzen, Messraster, Farben, Presets |
| `kkd_evaluation.py` | Messreihen, Kennzahlen, Verdikte |
| `kkd_layout.py` | Fester Kopf (Stylesheet) |
| `kkd_messungen.json`, `kkd_optima.json` | vorgerechnete Messreihen, eingefrorene Optima |
| `kkd_presets.py` | Permalink (Einrasten), Presets, Zufalls-Seed-Button |
| `kkd_scenario.py` | Handbeispiel, kleine Graphen, Beschreibung der Aufgabe |
| `kkd_visualization.py` | Plotly-Abbildungen (Achsen gesperrt) |
| `tests/` | Handrechnung, Orakel, Randfälle, Zweige, Verdikte, Claims, Presets, Layout, AppTest, Footer, Laufzeit-Importe |

## Bewusst nicht umgesetzt

Pseudo-Boolesche Nebenbedingungen mit Gewichten, ILP-Zähler, „genau k“ als eigene Kodierung, Kardinalitätsnetze (sortierende Netze), Mehrfachzähler, Zeitmessungen, weitere Löser, Industrieinstanzen, eine zweite Graphfamilie (Färbung mit Zählregel je Rampe). Das Totalizer-Original ist nicht beschafft.

## Lokal ausführen

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

pip install -r requirements.txt
streamlit run app.py
```

## Tests ausführen

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

Die vorgerechneten Messreihen neu schreiben: `python tools/messungen.py --alle` (mehrere Stunden, Python-CDCL); die Optima: `python tools/optima.py`.

## Einordnung und Quellen

- Sinz, Towards an optimal CNF encoding of Boolean cardinality constraints, CP 2005 (Volltext gelesen): Klauselzahl 2nk + n − 3k − 1, Hilfsvariablen (n − 1)k des sequentiellen Zählers und die Erkennung einer Verletzung durch Einheitspropagation. Bailleux und Boufkhad, CP 2003 (Totalizer): **Original nicht gelesen**, die Kodierung ist nach der Beschreibung bei Sinz gebaut.
- Der Vergleich Sinz-Zähler gegen Totalizer in Konflikten ist eine **eigene Messung** dieser Demo.
- Knotenüberdeckung als Reduktion von 3-SAT (ohne Zählregel): [reduktionskette-demo](https://github.com/sebastian-hanisch/reduktionskette-demo); Verzweigungsregeln im DPLL: [sat-phasenuebergang-demo](https://github.com/sebastian-hanisch/sat-phasenuebergang-demo); derselbe Konfliktgraph mit anderer Frage (Färbung): [graph-coloring-demo](https://github.com/sebastian-hanisch/graph-coloring-demo).

Gebaut mit Streamlit, Pandas und Plotly.

---

Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). Mehr zur Reihe: [SAT und CP: Konfliktlernen bis Wahl](https://sebastianhanisch.net/konzepte-sat-constraint-programming.html).
