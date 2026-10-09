"""Découpe les sources par arrêté et les convertit en Parquet (Lot 2, étape 3.2).

Hypothèses appliquées : H1 (T0), H2 (24 arrêtés, mois 0 exclu).
ENV=dev lit data/sample, sinon data/source.
"""
import os
import shutil
from pathlib import Path

import duckdb
from dotenv import load_dotenv

load_dotenv()
ENV = os.getenv("ENV", "dev")
T0 = os.getenv("T0_DATE", "2025-12-31")
NB_ARRETES = int(os.getenv("NB_ARRETES", "24"))
SOURCE = Path("data/sample" if ENV == "dev" else "data/source")
SORTIE = Path("data/preparation")

# table : (source métier, type de découpage)
TABLES = {
    "application_train": ("octroi", "photo"),
    "application_test": ("octroi", "photo"),
    "previous_application": ("octroi", "photo"),
    "bureau": ("bureau", "photo"),
    "bureau_balance": ("bureau", "mensuel"),
    "POS_CASH_balance": ("prets", "mensuel"),
    "credit_card_balance": ("monetique", "mensuel"),
    "installments_payments": ("recouvrement", "echeance"),
}

# Calcul de la date d'arrêté de chaque ligne
ARRETE = {
    "photo": f"DATE '{T0}'",
    "mensuel": f"last_day(DATE '{T0}' + to_months(CAST(MONTHS_BALANCE AS INTEGER)))",
    "echeance": f"last_day(DATE '{T0}' + CAST(CAST(DAYS_INSTALMENT AS DOUBLE) AS INTEGER))",
}

con = duckdb.connect()
debut, fin = con.execute(
    f"SELECT last_day(DATE '{T0}' + to_months(-{NB_ARRETES})), last_day(DATE '{T0}' + to_months(-1))"
).fetchone()
print(f"ENV={ENV} | source={SOURCE} | arrêtés du {debut} au {fin}")

if SORTIE.exists():
    shutil.rmtree(SORTIE)  # zone de préparation : régénérée à chaque exécution

for table, (source, type_) in TABLES.items():
    fichier = (SOURCE / f"{table}.csv").as_posix()
    dest = (SORTIE / f"source={source}" / f"table={table.lower()}").as_posix()
    Path(dest).mkdir(parents=True, exist_ok=True)  # crée aussi les dossiers parents
    filtre = "TRUE" if type_ == "photo" else f"arrete BETWEEN DATE '{debut}' AND DATE '{fin}'"
    con.execute(f"""
        COPY (
            SELECT * FROM (
                SELECT *, {ARRETE[type_]} AS arrete
                FROM read_csv('{fichier}', header=true, all_varchar=true)
            ) WHERE {filtre}
        ) TO '{dest}' (FORMAT PARQUET, PARTITION_BY (arrete))
    """)
    n_arretes, n_lignes = con.execute(
        f"SELECT count(DISTINCT arrete), count(*) FROM read_parquet('{dest}/**/*.parquet', hive_partitioning=true)"
    ).fetchone()
    print(f"{table:24} {n_arretes:>4} arrêté(s) {n_lignes:>12,} lignes")