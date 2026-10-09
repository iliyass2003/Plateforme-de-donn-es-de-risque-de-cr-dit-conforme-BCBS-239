# Image Airflow de la plateforme : Airflow 2 + un environnement Python séparé pour le projet
FROM apache/airflow:2.10.5-python3.11

USER airflow
COPY requirements.txt /tmp/requirements.txt
RUN python -m venv /opt/airflow/venv_projet \
 && /opt/airflow/venv_projet/bin/pip install --no-cache-dir -r /tmp/requirements.txt