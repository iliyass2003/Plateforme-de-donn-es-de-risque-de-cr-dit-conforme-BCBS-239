"""Profilage des sources Home Credit (Lot 2, étape 3.1).

Usage : python ingestion/landing/profilage.py [dossier_source]
Produit docs/profilage.md.
"""
import sys
from pathlib import Path

import duckdb
import pandas as pd

SOURCE = Path(sys.argv[1] if len(sys.argv) > 1 else "data/source")
SORTIE = Path("docs/profilage.md")
TABLES = [
    "application_train.csv", "application_test.csv", "bureau.csv", "bureau_balance.csv",
    "previous_application.csv", "POS_CASH_balance.csv", "credit_card_balance.csv",
    "installments_payments.csv",
]

con = duckdb.connect()
for nom in TABLES:
    vue = nom.replace(".csv", "").lower()
    con.execute(f"CREATE VIEW {vue} AS SELECT * FROM read_csv('{(SOURCE / nom).as_posix()}', header=true)")

rapport = ["# Rapport de profilage des sources", "", f"Source analysée : `{SOURCE.as_posix()}`", ""]


def section(titre, sql, commentaire):
    df = con.execute(sql).df()
    rapport.extend([f"## {titre}", "", commentaire, "", df.to_markdown(index=False), ""])
    print(f"\n=== {titre} ===\n{df.to_string(index=False)}")


# 1. Volumes et en-têtes (C2, C11)
lignes = []
for nom in TABLES:
    entete = (SOURCE / nom).open(encoding="latin-1").readline().rstrip("\r\n").split(",")
    vue = nom.replace(".csv", "").lower()
    lignes.append({
        "table": nom,
        "lignes": con.execute(f"SELECT count(*) FROM {vue}").fetchone()[0],
        "colonnes": len(entete),
        "noms_avec_espaces": ", ".join(repr(c) for c in entete if c != c.strip()) or "aucun",
    })
df = pd.DataFrame(lignes)
rapport.extend(["## 1. Volumes et en-têtes (C2)", "", "Nombre de lignes et de colonnes ; noms de colonnes contenant des espaces.", "", df.to_markdown(index=False), ""])
print(df.to_string(index=False))

section("2. Unicité des clés", """
    SELECT 'application_train.SK_ID_CURR' AS cle, count(*) AS lignes, count(DISTINCT SK_ID_CURR) AS distincts FROM application_train
    UNION ALL SELECT 'bureau.SK_ID_BUREAU', count(*), count(DISTINCT SK_ID_BUREAU) FROM bureau
    UNION ALL SELECT 'previous_application.SK_ID_PREV', count(*), count(DISTINCT SK_ID_PREV) FROM previous_application
""", "Une clé est unique si lignes = distincts.")

section("3. Lignes orphelines", """
    SELECT 'pos_cash -> previous_application' AS relation, count(*) AS orphelins
      FROM pos_cash_balance p ANTI JOIN previous_application v USING (SK_ID_PREV)
    UNION ALL SELECT 'credit_card -> previous_application', count(*)
      FROM credit_card_balance c ANTI JOIN previous_application v USING (SK_ID_PREV)
    UNION ALL SELECT 'installments -> previous_application', count(*)
      FROM installments_payments i ANTI JOIN previous_application v USING (SK_ID_PREV)
    UNION ALL SELECT 'bureau_balance -> bureau', count(*)
      FROM bureau_balance b ANTI JOIN bureau u USING (SK_ID_BUREAU)
""", "Nombre de lignes dont la clé n'existe pas dans la table parente.")

section("4. Valeur 365243 dans DAYS_EMPLOYED (H5)", """
    SELECT NAME_INCOME_TYPE, count(*) AS clients,
           count(*) FILTER (WHERE DAYS_EMPLOYED = 365243) AS valeur_365243
    FROM application_train GROUP BY 1 ORDER BY 3 DESC
""", "Si la valeur ne concerne que les retraités et les sans-emploi, H5 est confirmée.")

section("5. Retards de plus de 90 jours (H6)", """
    SELECT 'POS_CASH_balance' AS table_, count(*) FILTER (WHERE SK_DPD > 90) AS dpd_plus_90,
           count(*) FILTER (WHERE SK_DPD_DEF > 90) AS dpd_def_plus_90 FROM pos_cash_balance
    UNION ALL SELECT 'credit_card_balance', count(*) FILTER (WHERE SK_DPD > 90),
           count(*) FILTER (WHERE SK_DPD_DEF > 90) FROM credit_card_balance
""", "Écart entre retard brut (SK_DPD) et retard avec tolérance des petites dettes (SK_DPD_DEF).")

section("6. Profondeur des mois (H2, C6)", """
    SELECT 'bureau_balance' AS table_, min(MONTHS_BALANCE) AS mois_min, max(MONTHS_BALANCE) AS mois_max,
           count(*) FILTER (WHERE MONTHS_BALANCE = 0) AS lignes_mois_0 FROM bureau_balance
    UNION ALL SELECT 'POS_CASH_balance', min(MONTHS_BALANCE), max(MONTHS_BALANCE),
           count(*) FILTER (WHERE MONTHS_BALANCE = 0) FROM pos_cash_balance
    UNION ALL SELECT 'credit_card_balance', min(MONTHS_BALANCE), max(MONTHS_BALANCE),
           count(*) FILTER (WHERE MONTHS_BALANCE = 0) FROM credit_card_balance
""", "Jusqu'où remonte l'historique, et le mois 0 existe-t-il ?")

section("7. Devises du bureau (H3, C7)", """
    SELECT CREDIT_CURRENCY, count(*) AS credits FROM bureau GROUP BY 1 ORDER BY 2 DESC
""", "Si une devise domine largement, H3 (filtre sur la devise majoritaire) est applicable.")

section("8. Doublons de demandes passées (C8, H9)", """
    SELECT FLAG_LAST_APPL_PER_CONTRACT, NFLAG_LAST_APPL_IN_DAY, count(*) AS demandes
    FROM previous_application GROUP BY 1, 2 ORDER BY 3 DESC
""", "Les demandes marquées N ou 0 sont les doublons signalés par le dictionnaire.")

section("9. Plusieurs lignes par échéance (C10)", """
    SELECT count(*) AS echeances, count(*) FILTER (WHERE nb > 1) AS echeances_multi_lignes
    FROM (SELECT SK_ID_PREV, NUM_INSTALMENT_NUMBER, count(*) AS nb
          FROM installments_payments GROUP BY 1, 2)
""", "Si des échéances ont plusieurs lignes, le grain de la table est le paiement, pas l'échéance.")

SORTIE.write_text("\n".join(rapport), encoding="utf-8")
print(f"\nRapport écrit dans {SORTIE}")