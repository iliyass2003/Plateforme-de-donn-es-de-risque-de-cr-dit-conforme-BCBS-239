"""Publie les contrôles de l'arrêté et calcule le score qualité (Lot 6, étape 7.2).

Bloquant : RC-01 à RC-06. Avertissements : DQ-07 (quarantaine), DQ-11 (variation de l'encours).
Règle de publication (docs/gouvernance.md, 3.3) : aucun bloquant en KO ; score affiché.
"""
import os

import psycopg
from dotenv import load_dotenv

load_dotenv()
T0 = os.getenv("T0_DATE", "2025-12-31")
SEUIL_SCORE = 98.0

pg = psycopg.connect(
    host=os.getenv("POSTGRES_HOST", "localhost"), port=os.getenv("POSTGRES_PORT"), dbname=os.getenv("POSTGRES_DB"),
    user=os.getenv("POSTGRES_USER"), password=os.getenv("POSTGRES_PASSWORD"), autocommit=True,
)
pg.execute("SET ROLE role_transformation")

batch_id = pg.execute(
    "INSERT INTO ctl.batch_log (arrete, statut, message) VALUES (%s, 'EN_COURS', 'controles') RETURNING batch_id",
    (T0,),
).fetchone()[0]

try:
    # 1. Archiver la réconciliation (RC-01 à RC-06), bloquante
    pg.execute("""
        INSERT INTO ctl.reconciliation
            (batch_id, controle_id, indicateur, valeur_source, valeur_cible, ecart_relatif, tolerance, statut)
        SELECT %s, controle_id, indicateur || ' (' || arrete || ')',
               coalesce(valeur_source, 0), coalesce(valeur_cible, 0), ecart_relatif, tolerance, statut
        FROM ctl.rc_reconciliation
    """, (batch_id,))
    pg.execute("""
        INSERT INTO ctl.control_results (batch_id, controle_id, couche, gravite, statut, valeur, seuil, message)
        SELECT %s, controle_id, 'gold', 'BLOQUANT', statut, ecart_relatif, tolerance, indicateur || ' (' || arrete || ')'
        FROM ctl.rc_reconciliation
    """, (batch_id,))

    # 2. DQ-07 : taux de rejet en quarantaine par entité (avertissement si > 0,5 %)
    pg.execute("""
        INSERT INTO ctl.control_results (batch_id, controle_id, couche, gravite, statut, valeur, seuil, message)
        WITH totaux AS (
            SELECT 'demandes' AS entite, count(*) AS total FROM staging.stg_homecredit__demandes
            UNION ALL SELECT 'demandes_passees', count(*) FROM staging.stg_homecredit__demandes_passees
            UNION ALL SELECT 'suivi_prets', count(*) FROM staging.stg_homecredit__suivi_prets
            UNION ALL SELECT 'suivi_cartes', count(*) FROM staging.stg_homecredit__suivi_cartes
            UNION ALL SELECT 'paiements', count(*) FROM staging.stg_homecredit__paiements
            UNION ALL SELECT 'credits_externes', count(*) FROM staging.stg_homecredit__credits_externes
        ),
        rejets AS (SELECT entite, count(DISTINCT cle) AS n FROM intermediate.int_quarantaine GROUP BY entite)
        SELECT %s, 'DQ-07', 'silver', 'AVERTISSEMENT',
               CASE WHEN coalesce(r.n, 0)::numeric / t.total <= 0.005 THEN 'OK' ELSE 'KO' END,
               coalesce(r.n, 0)::numeric / t.total, 0.005,
               t.entite || ' : ' || coalesce(r.n, 0) || ' rejet(s) sur ' || t.total
        FROM totaux t LEFT JOIN rejets r USING (entite)
    """, (batch_id,))

    # 3. DQ-11 : variation de l'encours total par rapport à l'arrêté précédent (avertissement si > 15 %)
    pg.execute("""
        INSERT INTO ctl.control_results (batch_id, controle_id, couche, gravite, statut, valeur, seuil, message)
        SELECT %s, 'DQ-11', 'gold', 'AVERTISSEMENT',
               CASE WHEN abs(variation) <= 0.15 THEN 'OK' ELSE 'KO' END,
               round(variation, 4), 0.15,
               'Encours ' || arrete || ' vs arrêté précédent : ' || round(100 * variation, 1) || ' %%'
        FROM (
            SELECT arrete, encours_total / nullif(lag(encours_total) OVER (ORDER BY arrete), 0) - 1 AS variation
            FROM marts.agg_synthese_arrete
        ) v
        WHERE variation IS NOT NULL
    """, (batch_id,))

    # 4. Score qualité : dernier lot de chaque contrôle, regroupé par dimension
    scores = pg.execute("""
        WITH dernier AS (SELECT controle_id, max(batch_id) AS b FROM ctl.control_results GROUP BY controle_id),
        res AS (
            SELECT r.controle_id, r.statut
            FROM ctl.control_results r JOIN dernier d ON d.controle_id = r.controle_id AND d.b = r.batch_id
        )
        SELECT CASE
                 WHEN controle_id IN ('DQ-01', 'RC-02', 'RC-03', 'RC-04', 'RC-05') THEN 'exactitude'
                 WHEN controle_id IN ('DQ-03', 'RC-01', 'RC-06', 'RC-07', 'DQ-07')          THEN 'completude'
                 WHEN controle_id IN ('DQ-12', 'DQ-13')                                        THEN 'actualite'
                 ELSE 'coherence'
               END AS dimension,
               round(100 * avg((statut = 'OK')::int), 2) AS score
        FROM res GROUP BY 1 ORDER BY 1
    """).fetchall()
    score_global = round(sum(s for _, s in scores) / len(scores), 2)
    for dimension, score in scores + [("global", score_global)]:
        pg.execute("INSERT INTO ctl.dq_score (batch_id, arrete, dimension, score) VALUES (%s, %s, %s, %s)",
                   (batch_id, T0, dimension, score))
        print(f"{dimension:12} {score:>7} %")

    # 5. Règle de publication
    bloquants_ko = pg.execute("""
        SELECT count(*) FROM ctl.control_results
        WHERE batch_id = %s AND gravite = 'BLOQUANT' AND statut = 'KO'
    """, (batch_id,)).fetchone()[0]
    if bloquants_ko:
        raise RuntimeError(f"{bloquants_ko} contrôle(s) bloquant(s) en KO : publication refusée")

    message = "publié" if score_global >= SEUIL_SCORE else f"publié avec alerte : score {score_global} % < {SEUIL_SCORE} %"
    pg.execute("UPDATE ctl.batch_log SET statut = 'PUBLIE', fin = now(), message = %s WHERE batch_id = %s",
               (message, batch_id))
    print(f"Lot {batch_id} : {message}")
except Exception as erreur:
    pg.execute("UPDATE ctl.batch_log SET statut = 'ECHEC', fin = now(), message = %s WHERE batch_id = %s",
               (str(erreur)[:500], batch_id))
    raise