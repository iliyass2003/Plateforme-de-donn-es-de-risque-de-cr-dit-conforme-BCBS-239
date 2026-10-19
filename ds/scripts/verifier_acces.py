"""Vérifie l'accès du projet Data Science : lecture du gold, écriture dans ds, refus ailleurs."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import text  # noqa: E402

from ecl.donnees import charger_config, charger_features, moteur  # noqa: E402

engine = moteur()
config = charger_config()
print(f"Configuration lue : LGD = {config['lgd']['valeur']}, graine = {config['reproductibilite']['graine']}")

df = charger_features(engine, "train")
print(f"Contrat respecté ; {len(df)} clients, {df.shape[1]} colonnes, taux de la cible = {df['defaut_observe'].mean():.2%}")

with engine.begin() as c:
    c.execute(text("CREATE TABLE ds.test_acces (x int)"))
    c.execute(text("DROP TABLE ds.test_acces"))
print("Écriture dans ds : autorisée")

try:
    with engine.begin() as c:
        c.execute(text("CREATE TABLE marts.test_acces (x int)"))
    print("Écriture dans marts : AUTORISÉE (anomalie !)")
except Exception:
    print("Écriture dans marts : refusée (attendu)")