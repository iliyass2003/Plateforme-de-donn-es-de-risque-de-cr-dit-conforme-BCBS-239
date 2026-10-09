"""Extrait les indicateurs macro du Maroc (API Banque mondiale) vers la landing (Lot 2, étape 3.4).

Hypothèse H4. Contrôle DQ-13 (actualité). Réponses déposées brutes dans MinIO.
"""
import hashlib
import json
import os
import time
from datetime import date

import boto3
import psycopg
import requests
from dotenv import load_dotenv

load_dotenv()
T0 = os.getenv("T0_DATE", "2025-12-31")
BUCKET = os.getenv("MINIO_BUCKET_LANDING", "landing")
INDICATEURS = {
    "NY.GDP.MKTP.KD.ZG": "croissance_pib_reel",
    "FP.CPI.TOTL.ZG": "inflation",
    "SL.UEM.TOTL.ZS": "chomage",
    "FR.INR.LEND": "taux_debiteur",
}
ANCIENNETE_MAX = 2  # DQ-13 : dernière année disponible au plus 2 ans avant T0

s3 = boto3.client(
    "s3",
    endpoint_url=f"http://localhost:{os.getenv('MINIO_API_PORT')}",
    aws_access_key_id=os.getenv("MINIO_ROOT_USER"),
    aws_secret_access_key=os.getenv("MINIO_ROOT_PASSWORD"),
)
pg = psycopg.connect(
    host="localhost", port=os.getenv("POSTGRES_PORT"), dbname=os.getenv("POSTGRES_DB"),
    user=os.getenv("POSTGRES_USER"), password=os.getenv("POSTGRES_PASSWORD"), autocommit=True,
)
pg.execute("SET ROLE role_ingestion")


def appeler(code, tentatives=3):
    url = f"https://api.worldbank.org/v2/country/MAR/indicator/{code}?format=json&per_page=100"
    for essai in range(1, tentatives + 1):
        try:
            reponse = requests.get(url, timeout=30)
            reponse.raise_for_status()
            return reponse.content
        except requests.RequestException as erreur:
            print(f"  {code} : tentative {essai} échouée ({erreur})")
            if essai == tentatives:
                raise
            time.sleep(5)


batch_id = pg.execute(
    "INSERT INTO ctl.batch_log (arrete, statut) VALUES (%s, 'EN_COURS') RETURNING batch_id", (T0,)
).fetchone()[0]
try:
    jour = date.today().isoformat()
    for code, nom in INDICATEURS.items():
        brut = appeler(code)
        contenu = json.loads(brut)
        valeurs = contenu[1] if len(contenu) > 1 and contenu[1] else []
        annees = [int(v["date"]) for v in valeurs if v["value"] is not None]
        derniere = max(annees) if annees else None

        cle = f"source=banque_mondiale/table={nom}/date_extraction={jour}/data.json"
        empreinte = hashlib.sha256(brut).hexdigest()
        s3.put_object(Bucket=BUCKET, Key=cle, Body=brut)
        s3.put_object(Bucket=BUCKET, Key=cle.replace("data.json", "manifest.json"),
                      Body=json.dumps({"indicateur": code, "annees_renseignees": len(annees),
                                       "derniere_annee": derniere, "sha256": empreinte}, indent=2).encode())
        pg.execute(
            """INSERT INTO ctl.file_manifest
               (batch_id, source, table_name, arrete, chemin_objet, nb_lignes, sha256, sommes)
               VALUES (%s, 'banque_mondiale', %s, %s, %s, %s, %s, %s::jsonb)""",
            (batch_id, nom, T0, cle, len(annees), empreinte, json.dumps({"derniere_annee": derniere})),
        )

        a_jour = derniere is not None and int(T0[:4]) - derniere <= ANCIENNETE_MAX
        pg.execute(
            """INSERT INTO ctl.control_results
               (batch_id, controle_id, couche, gravite, statut, valeur, seuil, message)
               VALUES (%s, 'DQ-13', 'api', 'AVERTISSEMENT', %s, %s, %s, %s)""",
            (batch_id, "OK" if a_jour else "KO", derniere, int(T0[:4]) - ANCIENNETE_MAX,
             f"{code} : dernière année {derniere}"),
        )
        print(f"{nom:22} {len(annees):>3} années, dernière : {derniere}  -> DQ-13 {'OK' if a_jour else 'KO'}")

    pg.execute("UPDATE ctl.batch_log SET statut = 'SUCCES', fin = now(), message = 'API Banque mondiale' WHERE batch_id = %s",
               (batch_id,))
except Exception as erreur:
    pg.execute("UPDATE ctl.batch_log SET statut = 'ECHEC', fin = now(), message = %s WHERE batch_id = %s",
               (str(erreur)[:500], batch_id))
    raise