"""Kardinalität kodieren - interaktive Konzept-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Ein Löser kennt nur Klauseln. Wer „höchstens k von n“ sagen will, muss die Zählregel in Klauseln übersetzen: binomial, mit dem Sinz-Zähler oder mit dem
Totalizer. Die Demo zeigt die Übersetzung an einer kleinen Regel von Hand, wie die Größe wächst und was die Wahl an einer Frage im Konfliktgraphen
(Kontrollpunkte für Aufträge mit Unverträglichkeiten) in Konflikten ausmacht. Die großen Messreihen sind vorgerechnet (nicht live).

Lauffähig mit: streamlit run app.py
"""

import pandas as pd
import streamlit as st

import kkd_algorithm as A
import kkd_constants as C
import kkd_evaluation as E
import kkd_fortschritt as F
import kkd_scenario as S
import kkd_visualization as V
from kkd_layout import dunkles_design, kopf_css
from kkd_presets import (
    BELEGUNG_KEY,
    init_session_state_defaults,
    load_permalink_settings,
    randomize_seed,
    sidebar_presets,
    sync_query_params,
)

st.set_page_config(page_title="Kardinalität kodieren – Sebastian Hanisch", layout="wide")


@st.cache_data(show_spinner=False)
def _kodierung(n, k, verfahren):
    return A.kodierung(n, k, verfahren)


@st.cache_data(show_spinner=False)
def _semantik(verfahren, n, k):
    return A.semantik_pruefen(verfahren, n, k)


@st.cache_data(show_spinner=False)
def _wachstum(achse, fest):
    return E.wachstum(achse, fest)


@st.cache_data(show_spinner=False)
def _vollstaendig(art, seed):
    if art == "alle":
        n, k = C.E4_ALLE
        bel = list(A.alle_teilbelegungen(n))
    else:
        n, k, anzahl = C.E4_ZUFALL
        bel = A.zufalls_teilbelegungen(n, anzahl, seed)
    return {v: A.vollstaendigkeit(v, n, k, bel) for v in C.VERFAHREN}


# --- Kopf, Einleitung ----------------------------------------------------------------------------------------------------------------------

st.html(kopf_css(dunkles_design()))
with st.container(key="kopf"):
    st.title("🧮 Kardinalität kodieren")
st.markdown(
    """
Ein Löser, der aus Konflikten lernt, kennt nur **Klauseln**. Eine Zählregel wie „**höchstens k von n** Aufträgen dürfen kontrolliert werden“ muss er als
Klauseln lesen. Die naheliegende Übersetzung verbietet jede Auswahl von k + 1 Aufträgen einzeln (**binomial**); der **Sinz-Zähler** und der **Totalizer**
führen Hilfsvariablen ein, die mitzählen. Alle drei sagen dasselbe, ihre **Größe** und der **Suchverlauf** des Lösers (in **Konflikten**, nie in Sekunden)
unterscheiden sich. Dieselbe Frage kommt in der Linie später beim MaxSAT wieder, dort als Schranke.

Weiter unten: vier Experimente (**Eine Regel von Hand**, **Wie wächst die Kodierung**, **Dieselbe Frage, drei Kodierungen**, **Ist die Einheitspropagation
vollständig**), **🚧 Wo die Annahmen enden** und der Expander **📐 Mathematische Formulierung**.
"""
)

with st.expander("So funktioniert die Übersetzung einer Zählregel", expanded=True):
    st.markdown(
        """
1. **Binomial.** Von je k + 1 Eingängen ist mindestens einer falsch: eine Klausel (¬xᵢ ∨ ¬xⱼ ∨ …) für **jede** Auswahl von k + 1 Eingängen. Keine Hilfsvariable,
   aber C(n, k + 1) Klauseln.
2. **Sinz-Zähler (sequentieller Zähler).** Hilfsvariablen sᵢⱼ heißen „unter den ersten i Eingängen sind mindestens j wahr“. Jede Zeile gibt den Zählstand an die
   nächste weiter; ist ein k + 1-ter Eingang wahr, ist eine Klausel verletzt. Das sind 2nk + n − 3k − 1 Klauseln und (n − 1)k Hilfsvariablen (Sinz 2005).
3. **Totalizer.** Die Eingänge sind die Blätter eines Addierbaums; jeder Knoten hat Ausgänge oⱼ „mindestens j der Blätter darunter sind wahr“ (in Einerdarstellung,
   bei k + 1 Ausgängen abgeschnitten). Die Wurzel verbietet den Ausgang o_{k+1}. Hier nach der Beschreibung bei Sinz gebaut, das Original ist nicht gelesen.
4. **Der Löser** bekommt nur die Klauseln. Wie viele Konflikte er braucht, misst die Demo an der Frage „höchstens k Kontrollpunkte im Konfliktgraphen“ (Vertex Cover).
        """
    )

st.caption("🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, um ein Szenario zu teilen.")

load_permalink_settings()
init_session_state_defaults()

with st.sidebar:
    sidebar_presets()  # Schnellstart oben, das aktive Preset ist hervorgehoben
    st.header("⚙️ Einstellungen")
    st.markdown("**Experiment 3 (Löser)**")
    budget = st.select_slider("Konfliktbudget", C.BUDGET_OPTIONEN, key="budget", format_func=E.zahl,
                              help="Höchstens so viele Konflikte je Lauf. Ein Lauf, der das Budget erreicht, antwortet „unbekannt“, nie „unerfüllbar“, und zählt mit dem Budget. "
                                   "Die vorgerechneten Messreihen stehen auf 300.000.")
    st.markdown("**Experiment 4 (Zufallsteilbelegungen)**")
    st.number_input("Zufalls-Seed", 0, C.SEED_MAX, step=1, key="seed",
                    help="Bestimmt die 5.000 Zufallsteilbelegungen von Experiment 4 (SplitMix64, auf jeder Plattform gleich).")
    st.button("🎲 Neuer Zufalls-Seed", on_click=randomize_seed, width="stretch")

# --- Experiment 1: eine Regel von Hand --------------------------------------------------------------------------------------------------------

st.markdown("## 🔬 Experiment 1: Eine Regel von Hand")
st.caption("Wählen Sie n, k und die Kodierung; setzen Sie Eingänge auf wahr oder falsch. Die Einheitspropagation zeigt, was der Löser daraus ohne Suche folgert.")
c1, c2, c3 = st.columns([1, 1, 2])
n1 = int(c1.slider("Eingänge n", *C.E1_N, key="e1_n"))
k1 = int(c2.slider("Schranke k (höchstens k wahr)", *C.E1_K, key="e1_k", help="Bei k ≥ n ist die Regel nie verletzt: keine Klausel nötig."))
v_label = c3.radio("Kodierung", list(C.VERFAHREN_LABEL.values()), horizontal=True, key="e1_verfahren")
v1 = C.LABEL_VERFAHREN[v_label]
kod = _kodierung(n1, k1, v1)

formel_text = {
    "binomial": f"C({n1}, {k1 + 1}) = {A.klauselzahl('binomial', n1, k1):,}".replace(",", "."),
    "sinz": f"2·{n1}·{k1} + {n1} − 3·{k1} − 1 = {A.klauselzahl('sinz', n1, k1)}; (n − 1)·k = {A.hilfsvariablen('sinz', n1, k1)}" if 1 <= k1 < n1 else "k = 0: n Einheitsklauseln",
    "totalizer": "Rekursion über den Addierbaum (siehe 📐 unten)",
}[v1]
m1, m2, m3 = st.columns([1, 1, 3])
m1.metric("Klauseln", len(kod.klauseln))
m2.metric("Hilfsvariablen", kod.n_gesamt - n1)
m3.caption(f"Formel: {formel_text if k1 < n1 else 'k ≥ n: keine Klausel'}.")
if k1 >= n1:
    st.info(f"Bei k = {k1} ≥ n = {n1} ist „höchstens {k1} von {n1}“ immer erfüllt: die Kodierung braucht keine Klausel.")

st.markdown("**Eingänge setzen** (offen, wahr oder falsch)")
spalten = st.columns(n1)
feste = {}
for i in range(1, n1 + 1):
    wahl = spalten[i - 1].selectbox(f"x{i}", C.E1_BELEGUNG, key=BELEGUNG_KEY.format(i))
    if wahl != "offen":
        feste[i] = wahl == "wahr"

prop = A.propagiere(kod.klauseln, kod.n_gesamt, feste)
if prop.konflikt is not None:
    st.error(f"**Konflikt:** die Klausel {A.klausel_text(kod.klauseln[prop.konflikt], kod.namen)} ({kod.gruppen[prop.konflikt]}) ist verletzt. "
             f"Mehr als {k1} Eingänge wären wahr; der Löser merkt das ohne Suche, allein durch Einheitspropagation.")
elif not feste:
    st.info("Noch kein Eingang gesetzt: Setzen Sie zum Beispiel x1 und x2 auf wahr, um die Einheitspropagation zu sehen.")
elif prop.schritte:
    folgen = [A.literal_text(l, kod.namen) for l, _ in prop.schritte if abs(l) <= n1]
    st.success("Einheitspropagation: " + (", ".join(folgen) if folgen else "keine Eingänge erzwungen") + f" ({len(prop.schritte)} {'Schluss' if len(prop.schritte) == 1 else 'Schlüsse'}, davon {len(folgen)} an Eingängen).")
else:
    st.info("Aus den gesetzten Eingängen folgt nichts: die Einheitspropagation setzt nichts weiter.")

if prop.schritte or prop.konflikt is not None:
    with st.expander("Schlüsse Schritt für Schritt (mit auslösender Klausel)"):
        zeilen = [{"Nr": i + 1, "gesetzt": A.literal_text(l, kod.namen), "weil": A.klausel_text(kod.klauseln[g], kod.namen), "Gruppe": kod.gruppen[g]}
                  for i, (l, g) in enumerate(prop.schritte)]
        if prop.konflikt is not None:
            zeilen.append({"Nr": len(zeilen) + 1, "gesetzt": "Konflikt", "weil": A.klausel_text(kod.klauseln[prop.konflikt], kod.namen), "Gruppe": kod.gruppen[prop.konflikt]})
        st.dataframe(pd.DataFrame(zeilen), hide_index=True, width="stretch")

if kod.klauseln:
    with st.expander(f"Alle {len(kod.klauseln)} Klauseln mit Namen der Hilfsvariablen und Zustand unter der Belegung", expanded=True):
        belegung = prop.belegung
        zeilen = []
        for i, kl in enumerate(kod.klauseln):
            z = A.klauselzustand(kl, belegung)
            zeilen.append({"Nr": i + 1, "Gruppe": kod.gruppen[i], "Klausel": A.klausel_text(kl, kod.namen),
                           "Zustand": {"verletzt": "🔴 verletzt", "erfüllt": "erfüllt", "Einheit": "🟡 Einheit", "offen": "offen"}[z]})
        st.dataframe(pd.DataFrame(zeilen), hide_index=True, width="stretch")
        if v1 != "binomial" and k1 < n1:
            st.caption("Hilfsvariablen: " + ", ".join(f"{kod.namen[v]}" for v in range(n1 + 1, kod.n_gesamt + 1))
                       + (". sᵢⱼ: unter den ersten i Eingängen sind mindestens j wahr." if v1 == "sinz"
                          else ". oᴛⱼ: unter den Blättern des Knotens (W Wurzel, L links, R rechts) sind mindestens j wahr."))

if n1 <= C.SEMANTIK_MAX_N:
    geprueft, abw = _semantik(v1, n1, k1)
    st.caption(f"Prüfung durch Aufzählung: für alle {geprueft} Belegungen der Eingänge hat die Kodierung genau dann eine Fortsetzung auf die Hilfsvariablen, "
               f"wenn höchstens {k1} Eingänge wahr sind (Abweichungen: {abw}).")

st.markdown("---")

# --- Experiment 2: Wachstum --------------------------------------------------------------------------------------------------------------------

st.markdown("## 🔬 Experiment 2: Wie wächst die Kodierung?")
st.caption("Klauseln über n bei festem k (links) und über k bei festem n (rechts), logarithmische Achse. Linie: exakte Formel; Kreise: gebaute Kodierungen "
           f"(die binomiale Kodierung wird nur bis {E.zahl(C.BINOMIAL_GRENZE)} Klauseln gebaut, darüber zeigt die Demo nur die Formel).")
s1, s2 = st.columns(2)
k_fest = int(s1.slider("k fest (Achse über n)", *C.E2_K_FEST, key="e2_k"))
n_fest = int(s2.slider("n fest (Achse über k)", *C.E2_N_FEST, key="e2_n"))
w_n, w_k = _wachstum("n", k_fest), _wachstum("k", n_fest)
g1, g2 = st.columns(2)
g1.plotly_chart(V.build_wachstum(w_n["xs"], w_n["klauseln"], w_n["gebaut"], "Eingänge n", f"Klauseln über n bei k = {k_fest}", "Klauseln"),
                width="stretch", key="chart_wachstum_n")
g2.plotly_chart(V.build_wachstum(w_k["xs"], w_k["klauseln"], w_k["gebaut"], "Schranke k", f"Klauseln über k bei n = {n_fest}", "Klauseln"),
                width="stretch", key="chart_wachstum_k")
pt_kl = {v: A.klauselzahl(v, n_fest, k_fest) for v in C.VERFAHREN}
pt_hv = {v: A.hilfsvariablen(v, n_fest, k_fest) for v in C.VERFAHREN}
kind, text = E.verdict_groesse(n_fest, k_fest, pt_kl, pt_hv)
getattr(st, kind)(text)
st.dataframe(pd.DataFrame([{"Kodierung": C.VERFAHREN_LABEL[v], "Klauseln": pt_kl[v], "Hilfsvariablen": pt_hv[v],
                            "gebaut": "ja" if (v != "binomial" or pt_kl[v] <= C.BINOMIAL_GRENZE) else "nein (nur Formel)"} for v in C.VERFAHREN]),
             hide_index=True, width="stretch",
             column_config={"Klauseln": st.column_config.NumberColumn(format="localized"), "Hilfsvariablen": st.column_config.NumberColumn(format="localized")})

st.markdown("---")

# --- Experiment 3: dieselbe Frage, drei Kodierungen -------------------------------------------------------------------------------------------

st.markdown("## 🔬 Experiment 3: Dieselbe Frage, drei Kodierungen")
st.markdown(
    "**Die Frage:** In einem Konfliktgraphen (Aufträge, Kanten = Unverträglichkeiten) muss jede Unverträglichkeit an mindestens einem ihrer beiden Aufträge kontrolliert werden, "
    "und es dürfen höchstens **k** Kontrollpunkte sein (Vertex Cover höchstens k). Je Einstellung gibt es **10 feste Graphen**; k ist das Optimum des Graphen, "
    "das Optimum − 1 oder ein fester Wert. Das Optimum je Graph ist eingefroren (`kkd_optima.json`, bestimmt mit OR-Tools)."
)


def _waehle_festen_wert():
    st.session_state["e3_modus"] = "fester Wert k"


r1, r2, r3, r4 = st.columns([2, 1, 2, 2])
e3_n = int(r1.select_slider("Aufträge n", C.E3_N, key="e3_n"))
e3_grad = float(r2.radio("mittlerer Grad", C.E3_GRAD, key="e3_grad", format_func=lambda g: str(g).replace(".", ",")))
e3_modus = r3.radio("k", C.E3_MODI, key="e3_modus", horizontal=False)
e3_k = int(r4.slider("fester Wert k", *C.E3_K, key="e3_k", on_change=_waehle_festen_wert,
                     help="Bewegen Sie den Regler, wählt das den Modus „fester Wert k“: derselbe Wert k für alle zehn Graphen."))
k_arg = e3_k if e3_modus == "fester Wert k" else None
st.caption(S.beschreibung(e3_n, e3_grad) + f"; Optimum je Graph: {', '.join(str(A.optimum(e3_n, e3_grad, s)) for s in C.GRAPH_SEEDS)}.")


def _zelle_zeigen(zelle: dict, titel: str, kopfnote: str, schluessel: str):
    st.caption(kopfnote)
    kind, text = E.verdict_konflikte(zelle)
    getattr(st, kind)(text)
    roh = {v: zelle["verfahren"][v]["konflikte"] for v in C.VERFAHREN}
    st.plotly_chart(V.build_streifen(roh, zelle["budget"], titel), width="stretch", key=f"streifen_{schluessel}")
    zeilen = []
    for v in C.VERFAHREN:
        kz = E.kennzahlen(zelle, v)
        zeilen.append({"Kodierung": C.VERFAHREN_LABEL[v], "Klauseln (Median)": E.zahl_gross(kz.klauseln), "Hilfsvariablen (Median)": E.zahl(kz.hilfs),
                       "Konflikte Median": E.zahl(kz.median) if kz.gebaut else "nicht gebaut", "Minimum": E.zahl(kz.minimum) if kz.gebaut else "–",
                       "Maximum": E.zahl(kz.maximum) if kz.gebaut else "–", "Abbrüche am Budget": kz.abbrueche if kz.gebaut else "–",
                       "falsche Antworten": kz.falsche_antworten if kz.gebaut else "–"})
    st.dataframe(pd.DataFrame(zeilen), hide_index=True, width="stretch")


ref = E.referenz_zelle(e3_n, e3_grad, e3_modus, k_arg)
if not E.lade_messungen().get("zellen"):
    st.warning("Die vorgerechneten Messreihen (kkd_messungen.json) fehlen; nur die Live-Messreihe steht zur Verfügung.")
elif ref is None:
    st.info("Für diese Einstellung ist keine Messreihe vorgerechnet (vorgerechnet sind die Modi Optimum und Optimum − 1 für alle n und Grade, dazu die festen Werte "
            "n = 25 mit k = 5 und 8 sowie n = 60 mit k = 22 und 26). Eine Live-Messreihe steht darunter zur Verfügung.")
else:
    _zelle_zeigen(ref, f"Konflikte je Graph: n = {e3_n}, Grad {str(e3_grad).replace('.', ',')}",
                  f"Vorgerechnet, nicht live (Messskript tools/messungen.py, Datei kkd_messungen.json): 10 feste Graphen, Budget {E.zahl(ref['budget'])} Konflikte, "
                  "Python-CDCL mit Aktivität, Phasenspeicher und Luby-Neustarts (Einheit 32).", "ref")

with st.expander("🔁 Live nachrechnen"):
    st.caption("Dieselbe Messreihe mit dem Konfliktbudget der Seitenleiste, live gerechnet. Die binomiale Kodierung ist "
               "ab n = 25 bei fast allen k zu groß und wird dann nicht gebaut.")
    signatur = (e3_n, e3_grad, e3_modus, k_arg, budget)
    if st.button("Messreihe live starten", key="live_go",
                 help="Zehn Graphen, drei Kodierungen; je nach n und k dauert das unterschiedlich lang. Ein Fortschrittsbalken zählt die fertigen Läufe, "
                      "schon gerechnete Läufe kommen beim erneuten Start aus dem Zwischenspeicher."):
        with F.fortschrittsbalken("Die Messreihe läuft, fertige Läufe") as melde:
            st.session_state["live_e3"] = {"sig": signatur, "zelle": F.zelle(e3_n, e3_grad, e3_modus, k_arg, C.VERFAHREN, budget, melde)}
    gespeichert = st.session_state.get("live_e3")
    if gespeichert and gespeichert["sig"] == signatur:
        _zelle_zeigen(gespeichert["zelle"], f"Konflikte je Graph (live): n = {e3_n}, Grad {str(e3_grad).replace('.', ',')}",
                      f"Live gemessen, nicht vorgerechnet: 10 feste Graphen, Budget {E.zahl(budget)} Konflikte.", "live")
    elif gespeichert:
        st.caption("Die Einstellungen haben sich geändert: Messreihe erneut starten.")

st.markdown("---")

# --- Experiment 4: Vollständigkeit der Einheitspropagation -----------------------------------------------------------------------------------

st.markdown("## 🔬 Experiment 4: Ist die Einheitspropagation vollständig?")
st.markdown(
    "Die Regel „höchstens k“ erzwingt: sind **k** Eingänge wahr, müssen alle übrigen offenen falsch sein; sind **mehr als k** wahr, ist sie verletzt. "
    "Findet die Einheitspropagation jeden dieser Schlüsse allein aus den Klauseln? Geprüft wird an **allen** Teilbelegungen bei n = "
    f"{C.E4_ALLE[0]}, k = {C.E4_ALLE[1]} und an **{E.zahl(C.E4_ZUFALL[2])} Zufallsteilbelegungen** bei n = {C.E4_ZUFALL[0]}, k = {C.E4_ZUFALL[1]} (Zufalls-Seed der Seitenleiste)."
)
seed4 = int(st.session_state["seed"])
for art, (n4, k4) in (("alle", C.E4_ALLE), ("zufall", C.E4_ZUFALL[:2])):
    erg = _vollstaendig(art, seed4)
    st.markdown(f"**n = {n4}, k = {k4}: " + (f"alle {E.zahl(3 ** n4)} Teilbelegungen" if art == "alle" else f"{E.zahl(C.E4_ZUFALL[2])} Zufallsteilbelegungen, Zufalls-Seed {seed4}") + "**")
    kind, text = E.verdict_vollstaendigkeit(erg, n4, k4)
    getattr(st, kind)(text)
    st.dataframe(pd.DataFrame([{"Kodierung": C.VERFAHREN_LABEL[v], "Teilbelegungen": r.teilbelegungen, "Verletzungen": r.verletzungen,
                                "davon erkannt": r.verletzung_erkannt, "erzwungene Eingänge": r.erzwungen, "davon gefunden": r.erzwungen_erkannt,
                                "Teilbelegungen mit Lücke": r.mit_luecke, "falsch geschlossen": r.falsch_geschlossen} for v, r in erg.items()]),
                 hide_index=True, width="stretch")

st.markdown("---")

# --- Grenzen -------------------------------------------------------------------------------------------------------------------------------

st.subheader("🚧 Wo die Annahmen enden")
st.markdown(
    """
| Annahme | Was passiert, wenn sie verletzt ist | Wer setzt an |
|---|---|---|
| **Die Rangfolge Sinz-Zähler gegen Totalizer gilt allgemein** | Gemessen ist **eine** Graphfamilie (Zufallsgraphen mit mittlerem Grad 3 und 3,5, Vertex Cover höchstens k), zehn Graphen je Zelle und **ein** Löser (Python-CDCL mit Aktivität, Phasenspeicher, Luby-Neustarts). Bei anderen Familien oder Lösern kann sich die Rangfolge ändern; der Totalizer ist hier nach der Beschreibung bei Sinz gebaut, nicht nach dem Original. | – |
| **Weniger Konflikte heißt weniger Aufwand** | Die Konfliktzahl sagt nichts über den Speicher und nichts über die Zeit je Konflikt: bei n = 25, k = 5 braucht die binomiale Kodierung etwa so viele Konflikte wie die Zähler, aber viele hundertmal so viele Klauseln (Experiment 2 und 3). | Vorverarbeitung (eigene Demo der Linie) |
| **Die Einheitspropagation ist vollständig** | Ausgezählt ist sie nur für die Zellen von Experiment 4; darüber hinaus (andere n und k, Zähler mit weiteren Nebenbedingungen) macht die Demo keine Aussage. | – |
| **Nur „höchstens k“ mit gleichen Gewichten** | Gewichtete Nebenbedingungen (Pseudo-Boolesch), ILP-Zähler und „genau k“ als eigene Kodierung sind nicht gezeigt; „mindestens k“ ist „höchstens n − k“ der verneinten Eingänge. | MaxSAT (eigene Demo der Linie), Verfahrenswahl |
"""
)

st.markdown("---")

with st.expander("📐 Mathematische Formulierung"):
    st.markdown(
        r"""
**Gegeben und gesucht.** Gegeben sind Eingänge $x_1, \dots, x_n$ (Ja/Nein-Variablen) und eine Schranke $k$. Gesucht ist eine Klauselmenge, die genau dann (nach Wahl der Hilfsvariablen) erfüllt werden kann, wenn höchstens $k$ Eingänge wahr sind:
$$\sum_{i=1}^{n} x_i \le k$$

| Symbol | Bedeutung |
|---|---|
| $n$, $k$ | Zahl der Eingänge, Schranke (höchstens $k$ wahr) |
| $s_{i,j}$ | Sinz-Zähler: unter $x_1, \dots, x_i$ sind mindestens $j$ wahr ($1 \le i \le n-1$, $1 \le j \le k$) |
| $o^{(v)}_t$ | Totalizer: unter den Blättern unter dem Knoten $v$ sind mindestens $t$ wahr |
| $p_v$ | Zahl der Ausgänge des Knotens $v$ (Blatt: $p = 1$) |
| $w$ | Zahl der wahren Eingänge einer Teilbelegung |

**Binomial.** Von je $k+1$ Eingängen ist einer falsch:
$$\bigwedge_{S \subseteq \{1,\dots,n\},\ |S| = k+1}\ \bigvee_{i \in S} \neg x_i \qquad\text{mit}\qquad \binom{n}{k+1} \text{ Klauseln, keine Hilfsvariable.}$$

**Sinz-Zähler.** Klauseln für $1 < i < n$ und $1 < j \le k$:
$$(\neg x_1 \vee s_{1,1}), \qquad (\neg s_{1,j}), \qquad (\neg x_i \vee s_{i,1}), \qquad (\neg s_{i-1,1} \vee s_{i,1})$$
$$(\neg x_i \vee \neg s_{i-1,j-1} \vee s_{i,j}), \qquad (\neg s_{i-1,j} \vee s_{i,j}), \qquad (\neg x_i \vee \neg s_{i-1,k}), \qquad (\neg x_n \vee \neg s_{n-1,k})$$
Das sind genau
$$2nk + n - 3k - 1 \ \text{Klauseln und}\ (n-1)\,k \ \text{Hilfsvariablen} \qquad (1 \le k < n).$$

**Totalizer.** Ein Knoten $v$ mit Kindern $a$ und $b$ hat $p_v = \min(k+1,\, p_a + p_b)$ Ausgänge $o^{(v)}_1, \dots, o^{(v)}_{p_v}$; ein Blatt hat $p = 1$, sein einziger Ausgang ist der Eingang selbst. Für alle $0 \le i \le p_a$ und $0 \le j \le p_b$ mit $(i,j) \ne (0,0)$ gibt es die Klausel
$$(\neg o^{(a)}_i \vee \neg o^{(b)}_j \vee o^{(v)}_{\min(i+j,\ k+1)}) \qquad (\text{ein Literal entfällt für } i = 0 \text{ bzw. } j = 0),$$
und an der Wurzel die Schranke $(\neg o_{k+1})$. Für die Klauseln $c_v$ und die Hilfsvariablen $h_v$ des Teilbaums unter $v$ gilt (Blatt: $c = h = 0$):
$$c_v = c_a + c_b + (p_a + 1)(p_b + 1) - 1, \qquad h_v = h_a + h_b + p_v$$
und an der Wurzel kommt die Schranke als eine Klausel dazu, wenn $p > k$ ist. Der Baum teilt die Eingänge in der Mitte (bei $m$ Blättern $\lfloor m/2 \rfloor$ nach links).

**Kontrollpunkte (Vertex Cover höchstens $k$).** Für jede Kante $\{a, b\}$ des Konfliktgraphen die Klausel $(x_a \vee x_b)$, dazu die Zählregel über alle Aufträge:
$$\bigwedge_{\{a,b\} \in E} (x_a \vee x_b) \ \wedge\ \Big[\sum_{i=1}^{n} x_i \le k\Big]$$

**Was die Regel aus einer Teilbelegung folgert.** Mit $w$ wahren Eingängen gilt: bei $w > k$ ist die Regel verletzt, bei $w = k$ müssen alle offenen Eingänge falsch sein, bei $w < k$ ist nichts erzwungen (die Regel ist monoton: ein wahrer Eingang wird nie erzwungen):
$$\text{verletzt} \iff w > k, \qquad x_i \text{ erzwungen falsch} \iff w = k \ \wedge\ x_i \text{ offen}$$
Experiment 4 zählt, wie oft die Einheitspropagation dahinter zurückbleibt.

**Literatur.** Sinz, Towards an optimal CNF encoding of Boolean cardinality constraints, CP 2005 (Volltext gelesen: Klauselzahl $2nk + n - 3k - 1$, Hilfsvariablen $(n-1)k$, Erkennung einer Verletzung durch Einheitspropagation). Totalizer: Bailleux und Boufkhad, CP 2003; das Original ist nicht gelesen, die Kodierung ist nach der Beschreibung bei Sinz gebaut. Der Vergleich Sinz-Zähler gegen Totalizer in Konflikten ist eine eigene Messung dieser Demo, keine Aussage aus der Literatur.
        """
    )

sync_query_params({key: st.session_state[key] for key in ("seed", "budget", "e1_n", "e1_k", "e1_verfahren", "e2_n", "e2_k", "e3_n", "e3_grad", "e3_modus", "e3_k")})

st.markdown("---")
st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). "
    "Mehr zur Reihe: [SAT und CP: Konfliktlernen bis Wahl](https://sebastianhanisch.net/konzepte-sat-constraint-programming.html)."
)
