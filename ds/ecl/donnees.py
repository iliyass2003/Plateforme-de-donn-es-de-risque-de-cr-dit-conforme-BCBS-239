"""Accès aux données du gold pour le moteur ECL (lot DS-1).

Le projet lit seulement le gold, avec le compte svc_data_science (profil role_data_scientist),
et vérifie le contrat d'interface de mart_features_client avant tout usage.
"""
import os
from pathlib import Path

import pandas as pd
import yaml
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

RACINE = Path(__file__).resolve().parents[2]
load_dotenv(RACINE / ".env")

# Contrat d'interface : identique à dbt/credit_risk/models/marts/mart_features_client.yml
CONTRAT_FEATURES = {
    "client_id": "bigint", "origine": "text", "defaut_observe": "integer", "type_contrat": "text",
    "montant_credit": "numeric", "annuite": "numeric", "revenu_annuel": "numeric", "prix_bien": "numeric",
    "taux_effort": "numeric", "age": "integer", "nb_enfants": "integer", "niveau_etudes": "text",
    "type_revenu": "text", "est_sans_emploi": "boolean", "anciennete_emploi_annees": "numeric",
    "note_region": "integer", "score_externe_1": "numeric", "score_externe_2": "numeric",
    "score_externe_3": "numeric", "nb_credits_externes": "integer", "nb_credits_externes_actifs": "integer",
    "dette_externe": "numeric", "ratio_dette_externe_revenu": "numeric", "pire_retard_externe_jours": "integer",
    "pire_statut_externe_12m": "integer", "nb_demandes_passees": "integer", "taux_refus_passe": "numeric",
    "nb_paiements": "integer", "pct_paiements_en_retard": "numeric", "retard_paiement_max": "integer",
    "nb_echeances_non_payees": "integer", "utilisation_carte_moyenne": "numeric", "retard_carte_max": "integer",
}


def moteur():
    """Connexion au warehouse avec le compte Data Science."""
    url = (f"postgresql+psycopg://{os.getenv('DS_DB_USER')}:{os.getenv('DS_DB_PASSWORD')}"
           f"@{os.getenv('POSTGRES_HOST', 'localhost')}:{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DB')}")
    return create_engine(url)


def charger_config():
    """Les hypothèses expertes (M1 à M9) et paramètres du modèle."""
    with open(RACINE / "ds" / "config_hypotheses.yaml", encoding="utf-8") as f:
        return yaml.safe_load(f)


def verifier_contrat(engine):
    """Arrête tout si une colonne manque ou n'a pas le type attendu."""
    reel = pd.read_sql(text("""
        SELECT column_name, data_type FROM information_schema.columns
        WHERE table_schema = 'marts' AND table_name = 'mart_features_client'
    """), engine)
    reel = dict(zip(reel["column_name"], reel["data_type"]))
    erreurs = [f"  {col} : attendu {typ}, trouvé {reel.get(col, 'colonne absente')}"
               for col, typ in CONTRAT_FEATURES.items() if reel.get(col) != typ]
    if erreurs:
        raise ValueError("Contrat de mart_features_client non respecté :\n" + "\n".join(erreurs))


def charger_features(engine, origine="train"):
    """Clients d'une origine ('train' ou 'test'), après vérification du contrat."""
    verifier_contrat(engine)
    df = pd.read_sql(text("SELECT * FROM marts.mart_features_client WHERE origine = :o"),
                     engine, params={"o": origine})
    numeriques = [col for col, typ in CONTRAT_FEATURES.items() if typ == "numeric"]
    df[numeriques] = df[numeriques].astype(float)   # PostgreSQL renvoie des décimaux exacts
    return df