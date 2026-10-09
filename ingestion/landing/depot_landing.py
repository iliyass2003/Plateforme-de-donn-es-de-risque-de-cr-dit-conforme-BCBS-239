"""Dépose la zone de préparation dans la landing MinIO (Lot 2, étape 3.3).

BCBS 239 : P3 (empreintes SHA-256), P4 (comptages), piste d'audit dans ctl.
Un lot par arrêté. Relançable sans doublon.
"""
import hashlib
import json
import os
from collections import defaultdict
from pathlib import Path

import boto3
import duckdb
import psycopg
from dotenv import load_dotenv

load_dotenv()
PREPARATION = Path("data/preparation")
BUCKET = os.getenv("MINIO_BUCKET_LANDING", "landing")

# Montant de contrôle par table (servira à la réconciliation)
SOMMES = {
    "application_train": "AMT_CREDIT",
    "application_test": "AMT_CREDIT",
    "previous_application": "AMT_CREDIT",
    "bureau": "AMT_CREDIT_SUM",
    "credit_card_balance": "AMT_BALANCE",
    "installments_payments": "AMT_PAYMENT",
}

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
pg.execute("SET ROLE role_ingestion")  # on agit avec les droits du profil d'ingestion (P11)
duck = duckdb.connect()


def sha256(fichier):
    h = hashlib.sha256()
    with open(fichier, "rb") as f:
        for bloc in iter(lambda: f.read(1024 * 1024), b""):
            h.update(bloc)
    return h.hexdigest()


def attributs(fichier):
    # source=octroi/table=bureau/arrete=2025-12-31/data_0.parquet -> {source, table, arrete}
    return dict(p.split("=", 1) for p in fichier.relative_to(PREPARATION).parts[:-1])


par_arrete = defaultdict(list)
for fichier in sorted(PREPARATION.rglob("*.parquet")):
    par_arrete[attributs(fichier)["arrete"]].append(fichier)

for arrete, fichiers in sorted(par_arrete.items()):
    batch_id = pg.execute(
        "INSERT INTO ctl.batch_log (arrete, statut) VALUES (%s, 'EN_COURS') RETURNING batch_id", (arrete,)
    ).fetchone()[0]
    try:
        deposes = 0
        for fichier in fichiers:
            a = attributs(fichier)
            cle = fichier.relative_to(PREPARATION).as_posix()
            empreinte = sha256(fichier)
            if pg.execute("SELECT 1 FROM ctl.file_manifest WHERE chemin_objet = %s AND sha256 = %s",
                          (cle, empreinte)).fetchone():
                continue  # fichier identique déjà reçu

            chemin = fichier.as_posix()
            nb_lignes = duck.execute(f"SELECT count(*) FROM read_parquet('{chemin}')").fetchone()[0]
            sommes = {}
            if a["table"] in SOMMES:
                col = SOMMES[a["table"]]
                sommes[col] = duck.execute(
                    f"SELECT round(sum(TRY_CAST({col} AS DOUBLE)), 2) FROM read_parquet('{chemin}')"
                ).fetchone()[0]

            manifeste = {"table": a["table"], "arrete": arrete, "lignes": nb_lignes,
                         "sha256": empreinte, "sommes": sommes}
            s3.upload_file(chemin, BUCKET, cle, ExtraArgs={"Metadata": {"sha256": empreinte}})
            s3.put_object(Bucket=BUCKET, Key=cle.rsplit("/", 1)[0] + "/manifest.json",
                          Body=json.dumps(manifeste, indent=2).encode("utf-8"))
            pg.execute(
                """INSERT INTO ctl.file_manifest
                   (batch_id, source, table_name, arrete, chemin_objet, nb_lignes, sha256, sommes)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s::jsonb)""",
                (batch_id, a["source"], a["table"], arrete, cle, nb_lignes, empreinte, json.dumps(sommes)),
            )
            deposes += 1

        pg.execute("UPDATE ctl.batch_log SET statut = 'SUCCES', fin = now(), message = %s WHERE batch_id = %s",
                   (f"{deposes} fichier(s) déposé(s)", batch_id))
        print(f"Arrêté {arrete} : lot {batch_id}, {deposes}/{len(fichiers)} fichier(s) déposé(s)")
    except Exception as erreur:
        pg.execute("UPDATE ctl.batch_log SET statut = 'ECHEC', fin = now(), message = %s WHERE batch_id = %s",
                   (str(erreur)[:500], batch_id))
        raise