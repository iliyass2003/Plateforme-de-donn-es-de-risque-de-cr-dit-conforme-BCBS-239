"""Crée l'échantillon de développement (hypothèse H7).

Tire un pourcentage de clients au hasard (graine fixe) et garde
toutes leurs données liées dans les 8 tables.
"""
import os
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd
from dotenv import load_dotenv

load_dotenv()
TAUX = float(os.getenv("TAUX_ECHANTILLON_DEV", "0.10"))
GRAINE = int(os.getenv("GRAINE_ALEATOIRE", "42"))
SOURCE = Path("data/source")
SORTIE = Path("data/sample")
SORTIE.mkdir(parents=True, exist_ok=True)

con = duckdb.connect()


def lire(nom):
    # all_varchar : on garde les valeurs exactement comme dans la source
    return f"read_csv('{(SOURCE / nom).as_posix()}', header=true, all_varchar=true)"


# 1. Liste de tous les clients, puis tirage au hasard reproductible
ids = con.execute(f"""
    SELECT SK_ID_CURR FROM {lire('application_train.csv')}
    UNION
    SELECT SK_ID_CURR FROM {lire('application_test.csv')}
    ORDER BY 1
""").df()["SK_ID_CURR"].to_numpy()

rng = np.random.default_rng(GRAINE)
choisis = rng.choice(ids, size=round(len(ids) * TAUX), replace=False)
con.register("clients", pd.DataFrame({"SK_ID_CURR": choisis}))
print(f"Clients : {len(ids)} au total, {len(choisis)} retenus ({TAUX:.0%}, graine {GRAINE})")

# 2. Filtrer chaque table sur les clients retenus
tables = [
    "application_train.csv", "application_test.csv", "bureau.csv",
    "previous_application.csv", "POS_CASH_balance.csv",
    "credit_card_balance.csv", "installments_payments.csv",
]
for nom in tables:
    con.execute(f"""
        COPY (SELECT t.* FROM {lire(nom)} t
              WHERE t.SK_ID_CURR IN (SELECT SK_ID_CURR FROM clients))
        TO '{(SORTIE / nom).as_posix()}' (HEADER, DELIMITER ',')
    """)

# 3. bureau_balance n'a pas SK_ID_CURR : on passe par les crédits du bureau retenus
con.execute(f"""
    COPY (SELECT b.* FROM {lire('bureau_balance.csv')} b
          WHERE b.SK_ID_BUREAU IN (SELECT SK_ID_BUREAU FROM {lire('bureau.csv')}
                                   WHERE SK_ID_CURR IN (SELECT SK_ID_CURR FROM clients)))
    TO '{(SORTIE / 'bureau_balance.csv').as_posix()}' (HEADER, DELIMITER ',')
""")

# 4. Bilan : lignes source et échantillon par table
print(f"{'Table':32} {'Source':>12} {'Echantillon':>12} {'%':>6}")
for nom in tables + ["bureau_balance.csv"]:
    n_src = con.execute(f"SELECT count(*) FROM {lire(nom)}").fetchone()[0]
    n_ech = con.execute(f"SELECT count(*) FROM read_csv('{(SORTIE / nom).as_posix()}', header=true)").fetchone()[0]
    print(f"{nom:32} {n_src:>12,} {n_ech:>12,} {n_ech / n_src:>6.1%}")