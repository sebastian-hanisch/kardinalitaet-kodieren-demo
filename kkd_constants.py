"""Konstanten: Regler-Grenzen, feste Annahmen, Messraster der Experimente, Farben und Presets."""

# --- Kodierungen ----------------------------------------------------------------------------------------------------------------------------
VERFAHREN = ("binomial", "sinz", "totalizer")
VERFAHREN_LABEL = {"binomial": "Binomial", "sinz": "Sinz-Zähler", "totalizer": "Totalizer"}
LABEL_VERFAHREN = {v: k for k, v in VERFAHREN_LABEL.items()}
BINOMIAL_GRENZE = 400_000          # die binomiale Kodierung wird nur bis so vielen Klauseln gebaut; darüber zeigt die App nur die Formel C(n, k + 1)

# --- Experiment 1: eine Regel von Hand -------------------------------------------------------------------------------------------------------
E1_N = (3, 8)                      # Eingänge
E1_K = (0, 7)                      # Schranke (k >= n: die Regel ist immer erfüllt)
DEFAULT_E1_N, DEFAULT_E1_K, DEFAULT_E1_VERFAHREN = 4, 2, "Sinz-Zähler"
E1_BELEGUNG = ("offen", "wahr", "falsch")
SEMANTIK_MAX_N = 8                 # Aufzählung aller 2^n Eingaben höchstens bis n = 8

# --- Experiment 2: Wachstum ------------------------------------------------------------------------------------------------------------------
E2_N_FEST = (10, 60)               # Regler „n fest“ (Achse über k)
E2_K_FEST = (2, 10)                # Regler „k fest“ (Achse über n)
DEFAULT_E2_N, DEFAULT_E2_K = 25, 5
E2_N_PUNKTE = (6, 8, 10, 12, 15, 20, 25, 30, 40, 50, 60, 80, 100)     # Stützstellen über n
E2_K_PUNKTE = tuple(range(1, 31))                                      # Stützstellen über k

# --- Experiment 3: dieselbe Frage, drei Kodierungen ------------------------------------------------------------------------------------------
GRAPH_SEEDS = tuple(range(600, 610))   # 10 feste Konfliktgraphen je Zelle (SplitMix64): nie ein einzelner Seed als Befund
E3_N = (25, 30, 40, 50, 60)
E3_GRAD = (3.0, 3.5)
E3_MODI = ("Optimum", "Optimum − 1", "fester Wert k")
E3_K = (1, 60)
DEFAULT_E3_N, DEFAULT_E3_GRAD, DEFAULT_E3_MODUS, DEFAULT_E3_K = 25, 3.0, "Optimum", 5
BUDGET_OPTIONEN = (20_000, 50_000, 100_000, 300_000)
DEFAULT_BUDGET = 50_000
BUDGET_REFERENZ = 300_000          # Konfliktbudget der vorgerechneten Messreihen (kkd_messungen.json)
SCHWELLE_KAUM = 1.2                # Medianverhältnis, unter dem das Verdikt „kaum Unterschied“ sagt (mit der Zählung)
OPTIMA_DATEI = "kkd_optima.json"
MESSUNGEN_DATEI = "kkd_messungen.json"

# --- Experiment 4: Vollständigkeit der Einheitspropagation -----------------------------------------------------------------------------------
E4_ALLE = (6, 2)                   # n, k: alle 3^n Teilbelegungen (729)
E4_ZUFALL = (10, 3, 5000)          # n, k, Zahl der Zufallsteilbelegungen (SplitMix64)

# --- Allgemein --------------------------------------------------------------------------------------------------------------------------------
SEED_MAX, DEFAULT_SEED = 999999, 35

# --- Darstellung ------------------------------------------------------------------------------------------------------------------------------
COLOR = {"binomial": "#B5651D", "sinz": "#2F6B65", "totalizer": "#7A6FA8"}
COLOR_VERLETZT = "#C0392B"

# --- Presets ----------------------------------------------------------------------------------------------------------------------------------
# Schlüssel eines Presets = Schlüssel der Regler (siehe kkd_presets.PRESET_KEYS); fehlt einer, gilt die Voreinstellung.
# Das erste Preset entspricht den Voreinstellungen.
PRESETS = {
    "Handbeispiel": {"e1_n": 4, "e1_k": 2, "e1_verfahren": "Sinz-Zähler", "e1_belegung": {1: "wahr", 2: "wahr"}},
    "Klein und gleich": {"e3_n": 25, "e3_grad": 3.0, "e3_modus": "fester Wert k", "e3_k": 5},
    "Am Optimum": {"e3_n": 40, "e3_grad": 3.0, "e3_modus": "Optimum"},
    "Knapp unter dem Optimum": {"e3_n": 40, "e3_grad": 3.0, "e3_modus": "Optimum − 1"},
    "Deutlich unter dem Optimum": {"e3_n": 60, "e3_grad": 3.0, "e3_modus": "fester Wert k", "e3_k": 22},
}
PRESET_HELP = {
    "Handbeispiel": "„Höchstens 2 von 4“ im Sinz-Zähler, x1 und x2 wahr gesetzt: die Einheitspropagation setzt x3 und x4 auf falsch. Experiment 3 steht auf n = 25 am Optimum.",
    "Klein und gleich": "25 Aufträge, höchstens 5 Kontrollpunkte (fester Wert, unerfüllbar): im Median 8,5 bis 10 Konflikte bei allen drei Kodierungen, aber die binomiale Kodierung hat 684-mal so viele Zählerklauseln wie der Sinz-Zähler.",
    "Am Optimum": "40 Aufträge, Grad 3, k = Optimum (erfüllbar): in dieser Zelle braucht der Sinz-Zähler im Median das 1,9-Fache der Konflikte des Totalizers; bei anderen Größen und Graphen kann es anders sein (Experiment 3).",
    "Knapp unter dem Optimum": "40 Aufträge, Grad 3, k = Optimum − 1 (unerfüllbar): kaum Unterschied im Median zwischen Sinz-Zähler und Totalizer (Verhältnis 1,1).",
    "Deutlich unter dem Optimum": "60 Aufträge, Grad 3, k = 22 (fester Wert, unerfüllbar, deutlich unter dem Optimum): der Sinz-Zähler braucht im Median das 1,7-Fache der Konflikte des Totalizers.",
}

# --- Vorgerechnete Zellen von Experiment 3 (tools/messungen.py schreibt sie nach kkd_messungen.json): (n, Grad, Modus, k fest) ----------------------------
REFERENZ_ZELLEN = tuple(
    [(n, g, m, None) for n in E3_N for g in E3_GRAD for m in ("Optimum", "Optimum − 1")]
    + [(25, 3.0, "fester Wert k", 5), (25, 3.0, "fester Wert k", 8), (60, 3.0, "fester Wert k", 22), (60, 3.0, "fester Wert k", 26)]
)
