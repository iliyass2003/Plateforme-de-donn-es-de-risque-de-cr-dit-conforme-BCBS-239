"""Test du contrôle DQ-01 : altère puis restaure un fichier de la landing.

Usage : python tests/test_dq01_alteration.py alterer|restaurer
"""
import os
import sys

import boto3
from dotenv import load_dotenv

load_dotenv()
BUCKET = os.getenv("MINIO_BUCKET_LANDING", "landing")
PREFIXE = "source=prets/table=pos_cash_balance/arrete=2025-11-30/"

s3 = boto3.client(
    "s3",
    endpoint_url=f"http://localhost:{os.getenv('MINIO_API_PORT')}",
    aws_access_key_id=os.getenv("MINIO_ROOT_USER"),
    aws_secret_access_key=os.getenv("MINIO_ROOT_PASSWORD"),
)
cle = next(o["Key"] for o in s3.list_objects_v2(Bucket=BUCKET, Prefix=PREFIXE)["Contents"]
           if o["Key"].endswith(".parquet"))

if sys.argv[1] == "alterer":
    s3.put_object(Bucket=BUCKET, Key=cle, Body=b"contenu altere volontairement")
    print(f"Fichier altéré : {cle}")
elif sys.argv[1] == "restaurer":
    versions = s3.list_object_versions(Bucket=BUCKET, Prefix=cle)["Versions"]
    derniere = next(v for v in versions if v["IsLatest"])
    s3.delete_object(Bucket=BUCKET, Key=cle, VersionId=derniere["VersionId"])
    print(f"Fausse version supprimée, {len(versions) - 1} version(s) restante(s) : {cle}")