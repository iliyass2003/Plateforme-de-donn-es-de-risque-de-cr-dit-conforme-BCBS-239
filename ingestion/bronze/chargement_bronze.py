"""Charge la landing (MinIO) dans le schéma bronze de PostgreSQL (Lot 3).

Contrôles bloquants : DQ-01 (empreinte = manifeste), DQ-03 (lignes chargées = manifeste).
Aucune transformation des valeurs. Idempotent par arrêté.
"""
import hashlib
import os
import tempfile
from collections import defaultdict
from pathlib import Path

import boto3
import duckdb
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
pg.execute("SET ROLE role_ingestion")  # les tables bronze appartiendront au profil d'ingestion
duck = duckdb.connect()


def sha256(fichier):
    h = hashlib.sha256()
    with open(fichier, "rb") as f:
        for bloc in iter(lambda: f.read(1024 * 1024), b""):
            h.update(bloc)
    return h.hexdigest()


def controle(batch_id, controle_id, ok, valeur, seuil, message):
    pg.execute(
        """INSERT INTO ctl.control_results
           (batch_id, controle_id, couche, gravite, statut, valeur, seuil, message)
           VALUES (%s, %s, 'bronze', 'BLOQUANT', %s, %s, %s, %s)""",
        (batch_id, controle_id, "OK" if ok else "KO", valeur, seuil, message),
    )
    if not ok:
        raise RuntimeError(f"{controle_id} en échec : {message}")


# Dernière version de chaque fichier Home Credit reçu
manifestes = pg.execute("""
    SELECT DISTINCT ON (chemin_objet) table_name, arrete, chemin_objet, nb_lignes, sha256
    FROM ctl.file_manifest
    WHERE source <> 'banque_mondiale'
    ORDER BY chemin_objet, id DESC
""").fetchall()
par_arrete = defaultdict(list)
for m in manifestes:
    par_arrete[m[1]].append(m)

with tempfile.TemporaryDirectory() as tmp:
    parquet, csv = Path(tmp) / "f.parquet", Path(tmp) / "f.csv"
    for arrete, fichiers in sorted(par_arrete.items()):
        batch_id = pg.execute(
            "INSERT INTO ctl.batch_log (arrete, statut, message) VALUES (%s, 'EN_COURS', 'bronze') RETURNING batch_id",
            (arrete,),
        ).fetchone()[0]
        try:
            for table, _, cle, nb_attendu, sha_attendu in fichiers:
                # DQ-01 : le fichier n'a pas été altéré depuis son dépôt
                s3.download_file(BUCKET, cle, str(parquet))
                conforme = sha256(parquet) == sha_attendu
                controle(batch_id, "DQ-01", conforme, None, None, f"{cle} : empreinte " + ("conforme au manifeste" if conforme else "DIFFÉRENTE du manifeste"))

                # Table bronze : toutes les colonnes en texte + colonnes techniques
                colonnes = [c[0].lower() for c in duck.execute(
                    f"DESCRIBE SELECT * FROM read_parquet('{parquet.as_posix()}')").fetchall()]
                pg.execute(f"""
                    CREATE TABLE IF NOT EXISTS bronze.{table} (
                        {", ".join(f'"{c}" TEXT' for c in colonnes)},
                        _batch_id BIGINT NOT NULL, _arrete DATE NOT NULL, _source_file TEXT NOT NULL,
                        _row_hash TEXT NOT NULL, _loaded_at TIMESTAMPTZ NOT NULL DEFAULT now())
                """)

                # Idempotence : on remplace l'arrêté s'il avait déjà été chargé
                pg.execute(f"DELETE FROM bronze.{table} WHERE _arrete = %s", (arrete,))

                duck.execute(f"""
                    COPY (SELECT t.*, {batch_id} AS _batch_id, DATE '{arrete}' AS _arrete,
                                 '{cle}' AS _source_file, md5(CAST(t AS VARCHAR)) AS _row_hash
                          FROM read_parquet('{parquet.as_posix()}') t)
                    TO '{csv.as_posix()}' (HEADER, DELIMITER ',')
                """)
                noms = ", ".join([f'"{c}"' for c in colonnes] + ["_batch_id", "_arrete", "_source_file", "_row_hash"])
                with pg.cursor() as cur, cur.copy(f"COPY bronze.{table} ({noms}) FROM STDIN WITH (FORMAT csv, HEADER true)") as copie:
                    with open(csv, "rb") as f:
                        while bloc := f.read(1024 * 1024):
                            copie.write(bloc)

                # DQ-03 : aucune ligne perdue
                nb = pg.execute(f"SELECT count(*) FROM bronze.{table} WHERE _source_file = %s", (cle,)).fetchone()[0]
                controle(batch_id, "DQ-03", nb == nb_attendu, nb, nb_attendu, f"{cle} : {nb} lignes / {nb_attendu} attendues")

            pg.execute("UPDATE ctl.batch_log SET statut = 'SUCCES', fin = now(), message = %s WHERE batch_id = %s",
                       (f"bronze : {len(fichiers)} fichier(s) chargé(s)", batch_id))
            print(f"Arrêté {arrete} : lot {batch_id}, {len(fichiers)} fichier(s) chargé(s)")
        except Exception as erreur:
            pg.execute("UPDATE ctl.batch_log SET statut = 'ECHEC', fin = now(), message = %s WHERE batch_id = %s",
                       (str(erreur)[:500], batch_id))
            raise