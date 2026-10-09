"""Contrôle DQ-12 : durée de traitement de l'arrêté (BCBS 239, P5).

Usage : python mesurer_delai.py <début de l'exécution, format ISO>
Avertissement si la durée dépasse le délai cible (2 heures).
"""
import os
import sys
from datetime import datetime, timezone

import psycopg
from dotenv import load_dotenv

load_dotenv()
T0 = os.getenv("T0_DATE", "2025-12-31")
DELAI_CIBLE_MIN = 120

debut = datetime.fromisoformat(sys.argv[1])
duree_min = round((datetime.now(timezone.utc) - debut).total_seconds() / 60, 1)
ok = duree_min <= DELAI_CIBLE_MIN

pg = psycopg.connect(
    host=os.getenv("POSTGRES_HOST", "localhost"), port=os.getenv("POSTGRES_PORT"), dbname=os.getenv("POSTGRES_DB"),
    user=os.getenv("POSTGRES_USER"), password=os.getenv("POSTGRES_PASSWORD"), autocommit=True,
)
pg.execute("SET ROLE role_transformation")
batch_id = pg.execute(
    "INSERT INTO ctl.batch_log (arrete, statut, fin, message) VALUES (%s, 'SUCCES', now(), 'mesure du délai') RETURNING batch_id",
    (T0,),
).fetchone()[0]
pg.execute(
    """INSERT INTO ctl.control_results (batch_id, controle_id, couche, gravite, statut, valeur, seuil, message)
       VALUES (%s, 'DQ-12', 'orchestration', 'AVERTISSEMENT', %s, %s, %s, %s)""",
    (batch_id, "OK" if ok else "KO", duree_min, DELAI_CIBLE_MIN,
     f"Arrêté traité en {duree_min} min (cible : {DELAI_CIBLE_MIN} min)"),
)
print(f"DQ-12 {'OK' if ok else 'KO'} : {duree_min} min (cible {DELAI_CIBLE_MIN} min)")