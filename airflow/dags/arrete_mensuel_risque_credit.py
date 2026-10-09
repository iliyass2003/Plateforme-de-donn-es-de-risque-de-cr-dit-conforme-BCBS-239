"""Arrêté mensuel du risque de crédit : de la découpe des fichiers à la publication.

BCBS 239 : P5 (actualité), P10 (fréquence). Chaque tâche est idempotente :
le DAG peut être relancé sans créer de doublon.
"""
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.bash import BashOperator

PROJET = "/opt/projet"
PY = "/opt/airflow/venv_projet/bin/python"
DBT = "/opt/airflow/venv_projet/bin/dbt"
DBT_DIR = f"{PROJET}/dbt/credit_risk"


def signaler_echec(context):
    """Appelé quand une tâche échoue définitivement (après ses tentatives) : alerte Telegram."""
    import os

    import requests

    ti = context["task_instance"]
    message = (f"ALERTE arrêté risque de crédit\nTâche en échec : {ti.task_id}\n"
               f"Exécution : {context['logical_date']}\nLogs : http://localhost:8090")
    print(message)
    jeton, chat = os.getenv("TELEGRAM_BOT_TOKEN"), os.getenv("TELEGRAM_CHAT_ID")
    if jeton and chat and jeton != "changer_moi":
        requests.post(f"https://api.telegram.org/bot{jeton}/sendMessage",
                      data={"chat_id": chat, "text": message}, timeout=10)


default_args = {
    "owner": "data_engineering",
    "retries": 2,
    "retry_delay": timedelta(minutes=2),
    "execution_timeout": timedelta(minutes=60),
    "on_failure_callback": signaler_echec,
}

with DAG(
    dag_id="arrete_mensuel_risque_credit",
    description="Arrêté mensuel du risque de crédit (BCBS 239)",
    start_date=datetime(2026, 1, 1),
    schedule="0 5 1 * *",          # le 1er de chaque mois à 5 h
    catchup=False,
    max_active_runs=1,
    default_args=default_args,
    tags=["risque_credit", "bcbs239"],
) as dag:

    decoupage = BashOperator(task_id="decoupage", cwd=PROJET,
                             bash_command=f"{PY} ingestion/landing/decoupage.py")
    depot_landing = BashOperator(task_id="depot_landing", cwd=PROJET,
                                 bash_command=f"{PY} ingestion/landing/depot_landing.py")
    extraire_api = BashOperator(task_id="extraire_api", cwd=PROJET,
                                bash_command=f"{PY} ingestion/api/banque_mondiale.py")
    chargement_bronze = BashOperator(task_id="chargement_bronze", cwd=PROJET,
                                     bash_command=f"{PY} ingestion/bronze/chargement_bronze.py")
    chargement_bronze_api = BashOperator(task_id="chargement_bronze_api", cwd=PROJET,
                                         bash_command=f"{PY} ingestion/bronze/chargement_bronze_api.py")
    dbt_seed = BashOperator(task_id="dbt_seed", cwd=DBT_DIR,
                            bash_command=f"{DBT} seed --profiles-dir .")
    dbt_run = BashOperator(task_id="dbt_run", cwd=DBT_DIR,
                           bash_command=f"{DBT} run --profiles-dir .")
    dbt_test = BashOperator(task_id="dbt_test", cwd=DBT_DIR,
                            bash_command=f"{DBT} test --profiles-dir . --exclude rc_reconciliation")
    publier_controles = BashOperator(task_id="publier_controles", cwd=PROJET, retries=0,
                                     bash_command=f"{PY} ingestion/controles/publier_controles.py")

    decoupage >> depot_landing >> chargement_bronze
    extraire_api >> chargement_bronze_api
    mesurer_delai = BashOperator(task_id="mesurer_delai", cwd=PROJET, retries=0, trigger_rule="all_done",
                                 bash_command=f"{PY} ingestion/controles/mesurer_delai.py {{{{ dag_run.start_date.isoformat() }}}}")

    [chargement_bronze, chargement_bronze_api] >> dbt_seed >> dbt_run >> dbt_test >> publier_controles >> mesurer_delai