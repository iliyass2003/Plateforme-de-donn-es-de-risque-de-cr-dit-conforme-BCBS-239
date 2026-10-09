"""Charge les réponses de l'API Banque mondiale dans bronze (Lot 3, étape 4.3).

Contrôles bloquants : DQ-01 (empreinte), DQ-03 (années renseignées = manifeste).
Valeurs gardées en texte, sans transformation. Idempotent par fichier.
"""
import hashlib
import json
import os

import boto3
import psycopg
from dotenv import load_dotenv

load_dotenv()
BUCKET = os.getenv("MINIO_BUCKET_LANDING", "landing")
s3 = boto3.client(
    "s3",
    endpoint_url=os.getenv("MINIO_ENDPOINT", f"http://localhost:{os.getenv('MINIO_API_PORT')}"),
    aws_access_key_id=os.getenv("MINIO_ROOT_USER"),
    aws_secret_access_key=os.getenv("MINIO_ROOT_PASSWORD"),
)
pg = psycopg.connect(
    host=os.getenv("POSTGRES_HOST", "localhost"), port=os.getenv("POSTGRES_PORT"), dbname=os.getenv("POSTGRES_DB"),
    user=os.getenv("POSTGRES_USER"), password=os.getenv("POSTGRES_PASSWORD"), autocommit=True,
)
pg.execute("SET ROLE role_ingestion")


def controle(batch_id, controle_id, ok, valeur, seuil, message):
    pg.execute(
        """INSERT INTO ctl.control_results
           (batch_id, controle_id, couche, gravite, statut, valeur, seuil, message)
           VALUES (%s, %s, 'bronze', 'BLOQUANT', %s, %s, %s, %s)""",
        (batch_id, controle_id, "OK" if ok else "KO", valeur, seuil, message),
    )
    if not ok:
        raise RuntimeError(f"{controle_id} en échec : {message}")


pg.execute("""
    CREATE TABLE IF NOT EXISTS bronze.banque_mondiale (
        indicateur_code TEXT, indicateur_nom TEXT, pays TEXT, annee TEXT, valeur TEXT,
        _batch_id BIGINT NOT NULL, _arrete DATE NOT NULL, _source_file TEXT NOT NULL,
        _loaded_at TIMESTAMPTZ NOT NULL DEFAULT now())
""")

manifestes = pg.execute("""
    SELECT DISTINCT ON (table_name) table_name, arrete, chemin_objet, nb_lignes, sha256
    FROM ctl.file_manifest WHERE source = 'banque_mondiale'
    ORDER BY table_name, id DESC
""").fetchall()

arrete = manifestes[0][1]
batch_id = pg.execute(
    "INSERT INTO ctl.batch_log (arrete, statut, message) VALUES (%s, 'EN_COURS', 'bronze API') RETURNING batch_id",
    (arrete,),
).fetchone()[0]
try:
    for nom, arrete, cle, nb_attendu, sha_attendu in manifestes:
        brut = s3.get_object(Bucket=BUCKET, Key=cle)["Body"].read()
        conforme = hashlib.sha256(brut).hexdigest() == sha_attendu
        controle(batch_id, "DQ-01", conforme, None, None,
                 f"{cle} : empreinte " + ("conforme au manifeste" if conforme else "DIFFÉRENTE du manifeste"))

        contenu = json.loads(brut)
        lignes = contenu[1] if len(contenu) > 1 and contenu[1] else []
        pg.execute("DELETE FROM bronze.banque_mondiale WHERE _source_file = %s", (cle,))
        with pg.cursor() as cur:
            cur.executemany(
                """INSERT INTO bronze.banque_mondiale
                   (indicateur_code, indicateur_nom, pays, annee, valeur, _batch_id, _arrete, _source_file)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
                [(l["indicator"]["id"], l["indicator"]["value"], l["countryiso3code"], l["date"],
                  None if l["value"] is None else str(l["value"]), batch_id, arrete, cle) for l in lignes],
            )

        nb = pg.execute("SELECT count(valeur) FROM bronze.banque_mondiale WHERE _source_file = %s", (cle,)).fetchone()[0]
        controle(batch_id, "DQ-03", nb == nb_attendu, nb, nb_attendu, f"{cle} : {nb} années renseignées / {nb_attendu} attendues")
        print(f"{nom:22} {len(lignes):>3} lignes chargées, {nb} années renseignées")

    pg.execute("UPDATE ctl.batch_log SET statut = 'SUCCES', fin = now(), message = 'bronze API' WHERE batch_id = %s",
               (batch_id,))
except Exception as erreur:
    pg.execute("UPDATE ctl.batch_log SET statut = 'ECHEC', fin = now(), message = %s WHERE batch_id = %s",
               (str(erreur)[:500], batch_id))
    raise