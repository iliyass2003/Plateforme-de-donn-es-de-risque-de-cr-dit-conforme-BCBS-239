"""
Allocation optimale du capital par RAROC (Bâle III) — projet Optimisation, lots OPT-0 à OPT-4.

Question : combien de crédits accorder dans chaque segment (produit x classe de risque) pour
créer le plus de valeur, sans dépasser le capital et en respectant les règles de la banque ?

Lancement, à la racine du projet (PostgreSQL démarré, .venv activé) :
    python optimisation/allocation_capital.py

Étapes :
    1. Données : PD de chaque client avec la scorecard en production (MLflow pd_scorecard@production)
    2. Segments : 2 produits x 5 classes de risque, avec PD, demande, marge, perte attendue, RAROC
    3. Modèle PLNE (Pyomo + HiGHS) : maximiser la valeur créée sous 6 contraintes
    4. Prix duals (capital, financement, coût du risque) + vérification par différence finie
    5. Sensibilité au capital disponible
    6. Scénarios de stress
    7. Comparaison avec une allocation proportionnelle à la demande
    8. Vérificateur indépendant + rapport Markdown + graphiques (+ MLflow si disponible)

Toutes les sorties vont dans optimisation/resultats/.
"""

import sys
from datetime import date
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

RACINE = Path(__file__).resolve().parents[1]
DS = RACINE / "ds"
SORTIES = RACINE / "optimisation" / "resultats"

# ---------------------------------------------------------------------------
# 0. HYPOTHÈSES (O1 à O12) — toutes modifiables ici et testées en stress
# ---------------------------------------------------------------------------
CONFIG = {
    # O2 : classes de risque définies par la PD de la scorecard (bornes en PD)
    "classes": {"A": (0.00, 0.03), "B": (0.03, 0.05), "C": (0.05, 0.08), "D": (0.08, 0.15), "E": (0.15, 1.01)},
    # O2 : produits (valeur de type_contrat -> nom court)
    "produits": {"Cash loans": "cash", "Revolving loans": "renouvelable"},
    # O8 : conditions par produit (taux annuels)
    "taux_client": {"cash": 0.12, "renouvelable": 0.18},
    "cout_financement": 0.03,
    "cout_gestion": {"cash": 0.02, "renouvelable": 0.04},
    "lgd": 0.45,                     # O4 : LGD réglementaire Bâle (fondation, non garanti)
    "rw": 0.75,                      # O5 : pondération Bâle, portefeuille de détail (approche standard)
    "ratio_capital": 0.12,           # O6 : ratio de solvabilité minimal Bank Al-Maghrib
    "rentabilite_minimale": 0.12,    # O7 : rentabilité demandée par les actionnaires (k)
    "concentration_max": 0.30,       # O9 : part maximale d'un segment dans la production
    "cout_risque_max": 0.03,         # O10 : perte attendue moyenne maximale de la production
    "part_capital": 0.50,            # O11 : capital disponible = 50 % du capital qu'il faudrait pour toute la demande
    "part_ressources": 0.80,         # O11 : ressources de financement = 80 % de la demande
    "taille_min_pct": 0.10,          # O12 : un segment ouvert sert au moins 10 % de sa demande
    "cout_fixe_pct": 0.005,          # O12 : coût fixe d'ouverture = 0,5 % de la demande du segment
}

SCENARIOS = {
    "Base": {},
    "PD x 1,5": {"choc_pd": 1.5},
    "Capital -20 %": {"choc_capital": 0.8},
    "Financement +2 pts": {"choc_financement": 0.02},
    "Sévère (les trois)": {"choc_pd": 1.5, "choc_capital": 0.8, "choc_financement": 0.02},
}

TOLERANCE = 1e-6


# ---------------------------------------------------------------------------
# 1. DONNÉES : PD de chaque client avec la scorecard en production
# ---------------------------------------------------------------------------
def charger_clients():
    """Clients d'apprentissage + PD donnée par pd_scorecard@production."""
    import mlflow

    sys.path.insert(0, str(DS))
    from ecl.donnees import charger_features, moteur

    mlflow.set_tracking_uri(f"sqlite:///{(DS / 'mlflow.db').as_posix()}")
    modele = mlflow.pyfunc.load_model("models:/pd_scorecard@production")
    entrees = modele.metadata.get_input_schema().input_names()

    clients = charger_features(moteur(), "train")
    clients["pd"] = modele.predict(clients[entrees])["pd"].to_numpy()
    return clients[["type_contrat", "montant_credit", "defaut_observe", "pd"]]


# ---------------------------------------------------------------------------
# 2. SEGMENTS : paramètres de chaque produit x classe
# ---------------------------------------------------------------------------
def construire_segments(clients, cfg):
    c = clients[clients["type_contrat"].isin(cfg["produits"])].copy()
    c["produit"] = c["type_contrat"].map(cfg["produits"])
    bornes = [b[0] for b in cfg["classes"].values()] + [list(cfg["classes"].values())[-1][1]]
    c["classe"] = pd.cut(c["pd"], bornes, labels=list(cfg["classes"]), right=False)

    seg = c.groupby(["produit", "classe"], observed=True).agg(
        clients=("pd", "size"),
        demande=("montant_credit", lambda s: s.sum() / 1e6),  # en MDH
        pd=("pd", "mean"),
        taux_observe=("defaut_observe", "mean"),
    )
    seg.index = [f"{p}_{k}" for p, k in seg.index]
    seg["produit"] = [s.split("_")[0] for s in seg.index]
    return seg


def calculer_parametres(seg, cfg, choc_pd=1.0, choc_capital=1.0, choc_financement=0.0):
    """Ajoute marge, perte attendue, capital, RAROC et valeur unitaire ; renvoie aussi les plafonds globaux."""
    s = seg.copy()
    s["pd_utilisee"] = (s["pd"] * choc_pd).clip(upper=1.0)
    s["marge_nette"] = [cfg["taux_client"][p] - (cfg["cout_financement"] + choc_financement) - cfg["cout_gestion"][p]
                        for p in s["produit"]]
    s["perte_attendue"] = s["pd_utilisee"] * cfg["lgd"]                 # EL par DH prêté
    s["capital_unitaire"] = cfg["ratio_capital"] * cfg["rw"]            # capital par DH prêté
    s["raroc"] = (s["marge_nette"] - s["perte_attendue"]) / s["capital_unitaire"]
    s["valeur_unitaire"] = s["marge_nette"] - s["perte_attendue"] - cfg["rentabilite_minimale"] * s["capital_unitaire"]
    s["taille_min"] = cfg["taille_min_pct"] * s["demande"]
    s["cout_fixe"] = cfg["cout_fixe_pct"] * s["demande"]

    besoin_capital = (s["capital_unitaire"] * s["demande"]).sum()
    plafonds = {
        "capital": cfg["part_capital"] * besoin_capital * choc_capital,
        "ressources": cfg["part_ressources"] * s["demande"].sum(),
        "cout_risque_max": cfg["cout_risque_max"],
        "concentration_max": cfg["concentration_max"],
    }
    return s, plafonds


# ---------------------------------------------------------------------------
# 3. MODÈLE PLNE (Pyomo + HiGHS)
# ---------------------------------------------------------------------------
def construire_modele(s, plafonds, y_fixes=None):
    import pyomo.environ as pyo

    m = pyo.ConcreteModel("allocation_capital")
    m.S = pyo.Set(initialize=list(s.index))
    m.x = pyo.Var(m.S, domain=pyo.NonNegativeReals)   # MDH accordés dans le segment
    if y_fixes is None:
        m.y = pyo.Var(m.S, domain=pyo.Binary)         # 1 si le segment est ouvert : PLNE
        Y = m.y
    else:
        # Segments ouverts fixés : les y deviennent des constantes, le problème est un vrai PL (duals disponibles)
        Y = {t: int(round(y_fixes[t])) for t in s.index}

    v, K, EL = s["valeur_unitaire"].to_dict(), s["capital_unitaire"].to_dict(), s["perte_attendue"].to_dict()
    D, L, F = s["demande"].to_dict(), s["taille_min"].to_dict(), s["cout_fixe"].to_dict()
    total = sum(m.x[t] for t in m.S)

    # Objectif : valeur créée = résultat ajusté du risque - rémunération du capital - coûts fixes
    m.objectif = pyo.Objective(expr=sum(v[t] * m.x[t] - F[t] * Y[t] for t in m.S), sense=pyo.maximize)

    m.c1_capital = pyo.Constraint(expr=sum(K[t] * m.x[t] for t in m.S) <= plafonds["capital"])
    m.c2_concentration = pyo.Constraint(m.S, rule=lambda m, t: m.x[t] <= plafonds["concentration_max"] * total)
    m.c3_cout_risque = pyo.Constraint(expr=sum(EL[t] * m.x[t] for t in m.S) <= plafonds["cout_risque_max"] * total)
    m.c4_demande = pyo.Constraint(m.S, rule=lambda m, t: m.x[t] <= D[t] * Y[t])
    m.c5_taille_min = pyo.Constraint(m.S, rule=lambda m, t: m.x[t] >= L[t] * Y[t])
    m.c6_financement = pyo.Constraint(expr=total <= plafonds["ressources"])
    return m


def resoudre(s, plafonds, y_fixes=None):
    """Résout le PLNE (ou le PL à y fixés, pour les duals). Renvoie x, y, valeur et duals."""
    import pyomo.environ as pyo

    m = construire_modele(s, plafonds, y_fixes)
    if y_fixes is not None:
        m.dual = pyo.Suffix(direction=pyo.Suffix.IMPORT)
    try:
        resultat = pyo.SolverFactory("appsi_highs").solve(m)
    except RuntimeError as erreur:
        if "duals" not in str(erreur):
            raise
        # Le solveur n'a pas fourni de duals : on résout sans eux, le prix du capital sera mesuré autrement
        m.del_component(m.dual)
        resultat = pyo.SolverFactory("appsi_highs").solve(m)
    if not pyo.check_optimal_termination(resultat):
        raise RuntimeError(f"Pas de solution optimale : {resultat.solver.termination_condition}")

    sortie = {
        "x": pd.Series({t: pyo.value(m.x[t]) for t in m.S}).clip(lower=0),
        "y": pd.Series({t: int(round(pyo.value(m.y[t]))) for t in m.S}) if y_fixes is None
        else pd.Series({t: int(round(y_fixes[t])) for t in m.S}),
        "valeur": pyo.value(m.objectif),
        "duals": {},
    }
    if y_fixes is not None:
        for nom in ["c1_capital", "c3_cout_risque", "c6_financement"]:
            try:
                sortie["duals"][nom] = abs(m.dual[getattr(m, nom)])
            except (KeyError, AttributeError):
                sortie["duals"][nom] = np.nan
    return sortie


def optimiser(s, plafonds):
    """PLNE, puis PL à y fixés pour les prix duals (un PLNE n'a pas de dual direct)."""
    plne = resoudre(s, plafonds)
    pl = resoudre(s, plafonds, y_fixes=plne["y"].to_dict())
    plne["duals"] = pl["duals"]
    if np.isnan(plne["duals"].get("c1_capital", np.nan)):
        plne["duals"]["c1_capital"] = prix_marginal_capital(s, plafonds, plne["y"].to_dict())
    return plne


def prix_marginal_capital(s, plafonds, y, delta_pct=0.001):
    """Vérification du dual : valeur gagnée par MDH de capital ajouté, à segments ouverts fixés."""
    delta = plafonds["capital"] * delta_pct
    base = resoudre(s, plafonds, y_fixes=y)["valeur"]
    plus = resoudre(s, {**plafonds, "capital": plafonds["capital"] + delta}, y_fixes=y)["valeur"]
    return (plus - base) / delta


# ---------------------------------------------------------------------------
# 4. INDICATEURS ET VÉRIFICATEUR INDÉPENDANT
# ---------------------------------------------------------------------------
def indicateurs(s, x, y):
    production = x.sum()
    capital = (s["capital_unitaire"] * x).sum()
    resultat = ((s["marge_nette"] - s["perte_attendue"]) * x).sum() - (s["cout_fixe"] * y).sum()
    return {
        "production_mdh": production,
        "capital_utilise_mdh": capital,
        "resultat_ajuste_mdh": resultat,
        "valeur_creee_mdh": resultat - CONFIG["rentabilite_minimale"] * capital,
        "raroc_portefeuille": resultat / capital if capital > 0 else np.nan,
        "cout_risque": (s["perte_attendue"] * x).sum() / production if production > 0 else np.nan,
        "segments_ouverts": int((x > TOLERANCE).sum()),
    }


def verifier(s, plafonds, x, y=None):
    """Recalcule chaque contrainte avec numpy, sans Pyomo. Renvoie la liste des violations."""
    y = (x > TOLERANCE).astype(int) if y is None else y
    total, tol = x.sum(), 1e-4 * max(1.0, x.sum())
    controles = {
        "C1 capital": (s["capital_unitaire"] * x).sum() <= plafonds["capital"] + tol,
        "C2 concentration": bool((x <= plafonds["concentration_max"] * total + tol).all()),
        "C3 coût du risque": (s["perte_attendue"] * x).sum() <= plafonds["cout_risque_max"] * total + tol,
        "C4 demande": bool((x <= s["demande"] * y + tol).all()),
        "C5 taille minimale": bool((x >= s["taille_min"] * y - tol).all()),
        "C6 financement": total <= plafonds["ressources"] + tol,
    }
    return [nom for nom, ok in controles.items() if not ok]


# ---------------------------------------------------------------------------
# 5. ALLOCATION DE RÉFÉRENCE : proportionnelle à la demande
# ---------------------------------------------------------------------------
def allocation_proportionnelle(s, plafonds):
    """Pratique simple : servir chaque segment au même pourcentage de sa demande, jusqu'au capital ou aux ressources."""
    capital_total = (s["capital_unitaire"] * s["demande"]).sum()
    taux = min(1.0, plafonds["capital"] / capital_total, plafonds["ressources"] / s["demande"].sum())
    return s["demande"] * taux


# ---------------------------------------------------------------------------
# 6. PROGRAMME PRINCIPAL
# ---------------------------------------------------------------------------
def tableau_md(df, decimales=2):
    df = df.copy()
    lignes = ["| " + " | ".join([df.index.name or ""] + [str(c) for c in df.columns]) + " |",
              "|" + " --- |" * (len(df.columns) + 1)]
    entiers = [c for c in df.columns if pd.api.types.is_integer_dtype(df[c])]
    for i in df.index:
        cellules = []
        for c in df.columns:
            v = df.at[i, c]
            if c in entiers:
                cellules.append(f"{int(v):,}".replace(",", " "))
            elif isinstance(v, (float, np.floating)):
                cellules.append(f"{v:,.{decimales}f}".replace(",", " "))
            else:
                cellules.append(str(v))
        lignes.append("| " + " | ".join([str(i)] + cellules) + " |")
    return "\n".join(lignes)


def executer(clients):
    SORTIES.mkdir(parents=True, exist_ok=True)

    # --- Segments et paramètres
    seg = construire_segments(clients, CONFIG)
    s, plafonds = calculer_parametres(seg, CONFIG)
    print(f"{len(s)} segments, demande totale {s['demande'].sum():,.0f} MDH")
    print(f"Capital disponible {plafonds['capital']:,.0f} MDH, ressources {plafonds['ressources']:,.0f} MDH\n")

    # --- Optimisation
    opt = optimiser(s, plafonds)
    x, y = opt["x"], opt["y"]
    violations = verifier(s, plafonds, x, y)
    pm = prix_marginal_capital(s, plafonds, y.to_dict())

    allocation = s[["clients", "demande", "pd", "taux_observe", "marge_nette", "perte_attendue", "raroc",
                    "valeur_unitaire"]].copy()
    allocation["ouvert"] = y
    allocation["accorde_mdh"] = x
    allocation["part_demande"] = np.where(s["demande"] > 0, x / s["demande"], 0)
    allocation["part_production"] = x / x.sum() if x.sum() > 0 else 0
    allocation.index.name = "segment"

    # --- Allocation proportionnelle
    x_prop = allocation_proportionnelle(s, plafonds)
    comparaison = pd.DataFrame({
        "Optimisation (PLNE)": indicateurs(s, x, y),
        "Proportionnelle": indicateurs(s, x_prop, (x_prop > TOLERANCE).astype(int)),
    })
    violations_prop = verifier(s, plafonds, x_prop)
    v_opt, v_prop = comparaison.loc["valeur_creee_mdh"]
    gain = (v_opt - v_prop) / abs(v_prop) if v_prop != 0 else np.nan

    # --- Sensibilité au capital
    sensibilite = []
    for part in np.arange(0.2, 1.21, 0.1):
        p = {**plafonds, "capital": plafonds["capital"] * part / CONFIG["part_capital"]}
        r = optimiser(s, p)
        sensibilite.append({"capital_pct_besoin": round(part * 100), "capital_mdh": p["capital"],
                            "valeur_creee_mdh": r["valeur"], "dual_capital": r["duals"].get("c1_capital", np.nan),
                            "production_mdh": r["x"].sum(), "segments_ouverts": int(r["y"].sum())})
    sensibilite = pd.DataFrame(sensibilite).set_index("capital_pct_besoin")

    # --- Stress : on ré-optimise, et on teste aussi l'allocation de base sous le choc
    stress = []
    for nom, choc in SCENARIOS.items():
        s_c, p_c = calculer_parametres(seg, CONFIG, **choc)
        r = optimiser(s_c, p_c)
        ind = indicateurs(s_c, r["x"], r["y"])
        ind_base = indicateurs(s_c, x, y)
        stress.append({
            "scenario": nom,
            "valeur_reoptimisee_mdh": r["valeur"],
            "production_mdh": ind["production_mdh"],
            "raroc_portefeuille": ind["raroc_portefeuille"],
            "segments_ouverts": ind["segments_ouverts"],
            "dual_capital": r["duals"].get("c1_capital", np.nan),
            "valeur_allocation_base_mdh": ind_base["valeur_creee_mdh"],
            "allocation_base_respecte": "oui" if not verifier(s_c, p_c, x, y) else "non : " + ", ".join(verifier(s_c, p_c, x, y)),
        })
    stress = pd.DataFrame(stress).set_index("scenario")

    # --- Fichiers CSV
    allocation.to_csv(SORTIES / "allocation_optimale.csv")
    comparaison.to_csv(SORTIES / "comparaison_proportionnelle.csv")
    sensibilite.to_csv(SORTIES / "sensibilite_capital.csv")
    stress.to_csv(SORTIES / "stress.csv")

    # --- Graphiques
    fig, ax = plt.subplots(figsize=(9, 4.5))
    ordre = allocation.sort_values("raroc", ascending=False)
    couleurs = ["#2E86C1" if o else "#BBBBBB" for o in ordre["ouvert"]]
    ax.bar(ordre.index, ordre["raroc"] * 100, color=couleurs)
    ax.axhline(CONFIG["rentabilite_minimale"] * 100, color="#C0392B", linestyle="--",
               label=f"Rentabilité minimale k = {CONFIG['rentabilite_minimale']:.0%}")
    ax.set_ylabel("RAROC (%)")
    ax.set_title("RAROC par segment (bleu = ouvert par l'optimisation)")
    ax.legend()
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.savefig(SORTIES / "raroc_par_segment.png", dpi=130)
    plt.close()

    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.bar(allocation.index, allocation["demande"], color="#D6EAF8", label="Demande")
    ax.bar(allocation.index, allocation["accorde_mdh"], color="#1F4E79", label="Accordé (optimal)")
    ax.set_ylabel("MDH")
    ax.set_title("Demande et montant accordé par segment")
    ax.legend()
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.savefig(SORTIES / "allocation_par_segment.png", dpi=130)
    plt.close()

    fig, ax1 = plt.subplots(figsize=(8, 4.5))
    ax1.plot(sensibilite["capital_mdh"], sensibilite["valeur_creee_mdh"], "o-", color="#1F4E79")
    ax1.set_xlabel("Capital disponible (MDH)")
    ax1.set_ylabel("Valeur créée (MDH)", color="#1F4E79")
    ax2 = ax1.twinx()
    ax2.step(sensibilite["capital_mdh"], sensibilite["dual_capital"], where="mid", color="#C0392B")
    ax2.set_ylabel("Prix dual du capital (MDH par MDH)", color="#C0392B")
    ax1.set_title("Valeur créée et prix dual selon le capital disponible")
    plt.tight_layout()
    plt.savefig(SORTIES / "sensibilite_capital.png", dpi=130)
    plt.close()

    # --- Rapport
    ind = comparaison["Optimisation (PLNE)"]
    duals = opt["duals"]
    hypotheses = pd.DataFrame({
        "Valeur": [f"{CONFIG['lgd']:.0%}", f"{CONFIG['rw']:.0%}", f"{CONFIG['ratio_capital']:.0%}",
                   f"{CONFIG['rentabilite_minimale']:.0%}", f"{CONFIG['concentration_max']:.0%}",
                   f"{CONFIG['cout_risque_max']:.0%}", f"{CONFIG['part_capital']:.0%} du besoin",
                   f"{CONFIG['part_ressources']:.0%} de la demande",
                   f"cash {CONFIG['taux_client']['cash']:.0%}, renouvelable {CONFIG['taux_client']['renouvelable']:.0%}",
                   f"{CONFIG['cout_financement']:.0%}"],
    }, index=pd.Index(["LGD (O4)", "Pondération Bâle RW (O5)", "Ratio de capital (O6)", "Rentabilité minimale k (O7)",
                       "Concentration max (O9)", "Coût du risque max (O10)", "Capital disponible (O11)",
                       "Ressources (O11)", "Taux client (O8)", "Coût de financement (O8)"], name="Hypothèse"))

    rapport = f"""# Allocation optimale du capital par RAROC

Généré le {date.today():%d/%m/%Y} par `optimisation/allocation_capital.py`.

## Résultat principal

- Valeur créée : **{ind['valeur_creee_mdh']:,.1f} MDH**, contre {v_prop:,.1f} MDH pour une allocation proportionnelle à la demande ({gain:+.0%}).
- RAROC du portefeuille : **{ind['raroc_portefeuille']:.1%}** (rentabilité minimale {CONFIG['rentabilite_minimale']:.0%}).
- Production : {ind['production_mdh']:,.0f} MDH ; capital utilisé : {ind['capital_utilise_mdh']:,.0f} / {plafonds['capital']:,.0f} MDH.
- Coût du risque : {ind['cout_risque']:.2%} (maximum {CONFIG['cout_risque_max']:.0%}) ; segments ouverts : {int(ind['segments_ouverts'])} / {len(s)}.
- Prix dual du capital : **{duals.get('c1_capital', np.nan):.3f}** MDH de valeur par MDH de capital en plus (vérification par différence finie : {pm:.3f}).
- Prix dual du coût du risque : {duals.get('c3_cout_risque', np.nan):.3f} ; du financement : {duals.get('c6_financement', np.nan):.3f}.
- Vérificateur indépendant : {"toutes les contraintes respectées" if not violations else "VIOLATIONS : " + ", ".join(violations)}.
- Allocation proportionnelle : {"respecte toutes les contraintes" if not violations_prop else "ne respecte pas : " + ", ".join(violations_prop)}.

## Hypothèses

{tableau_md(hypotheses)}

## Allocation par segment (montants en MDH)

{tableau_md(allocation, 3)}

## Comparaison avec l'allocation proportionnelle

{tableau_md(comparaison, 3)}

## Sensibilité au capital disponible

{tableau_md(sensibilite, 3)}

## Scénarios de stress

{tableau_md(stress, 3)}

## Graphiques

![RAROC par segment](raroc_par_segment.png)

![Allocation par segment](allocation_par_segment.png)

![Sensibilité au capital](sensibilite_capital.png)
"""
    (SORTIES / "rapport_allocation.md").write_text(rapport, encoding="utf-8")

    # --- Affichage console
    pd.set_option("display.width", 200)
    print("ALLOCATION OPTIMALE")
    print(allocation[["clients", "pd", "taux_observe", "raroc", "valeur_unitaire", "ouvert", "accorde_mdh",
                      "part_demande"]].round(4).to_string())
    print("\nCOMPARAISON")
    print(comparaison.round(4).to_string())
    print(f"\nGain de valeur vs proportionnelle : {gain:+.1%}")
    print(f"Allocation proportionnelle : {'OK' if not violations_prop else 'viole ' + ', '.join(violations_prop)}")
    print(f"\nDuals : {', '.join(f'{k} = {v:.4f}' for k, v in duals.items())}")
    print(f"Prix marginal du capital (différence finie) : {pm:.4f}")
    print(f"Vérificateur : {'OK' if not violations else 'VIOLATIONS ' + str(violations)}")
    print("\nSTRESS")
    print(stress.round(4).to_string())
    print(f"\nRésultats écrits dans {SORTIES}")

    return {"comparaison": comparaison, "duals": duals, "gain": gain, "violations": violations, "stress": stress,
            "plafonds": plafonds, "prix_marginal": pm}


def enregistrer_mlflow(res):
    try:
        import mlflow
    except ImportError:
        return
    mlflow.set_tracking_uri(f"sqlite:///{(DS / 'mlflow.db').as_posix()}")
    if mlflow.get_experiment_by_name("allocation_capital") is None:
        mlflow.create_experiment("allocation_capital", artifact_location=(DS / "mlruns").as_uri())
    mlflow.set_experiment("allocation_capital")
    ind = res["comparaison"]["Optimisation (PLNE)"]
    with mlflow.start_run(run_name="allocation_raroc_v1"):
        mlflow.log_params({k: v for k, v in CONFIG.items() if isinstance(v, (int, float))})
        mlflow.log_metrics({
            "valeur_creee_mdh": ind["valeur_creee_mdh"], "raroc_portefeuille": ind["raroc_portefeuille"],
            "cout_risque": ind["cout_risque"], "gain_vs_proportionnelle": res["gain"],
            "dual_capital": res["duals"].get("c1_capital", float("nan")), "prix_marginal_capital": res["prix_marginal"],
        })
        mlflow.log_artifacts(str(SORTIES))
        print("Run MLflow enregistrée :", mlflow.active_run().info.run_id)


if __name__ == "__main__":
    resultats = executer(charger_clients())
    enregistrer_mlflow(resultats)