# Matrice de conformité BCBS 239

Correspondance entre les principes BCBS 239 (Comité de Bâle, 2013) et leur mise en œuvre dans la plateforme. La colonne « Preuve » est complétée au fil des lots.

| Version | Date | Modification |
| --- | --- | --- |
| 1.0 | 2026-10-04 | Création, preuves à compléter |

| Principe | Exigence dans le projet | Lot | Preuve | Statut |
| --- | --- | --- | --- | --- |
| P1 Gouvernance | Propriétaires désignés, politique qualité écrite | 0 | `docs/gouvernance.md` | Fait |
| P2 Architecture et infrastructure | Architecture en couches, dictionnaire unique, identifiants cohérents | 0, 5 | `docs/architecture.md`, `docs/dictionnaire_sources.md`, lignage dbt `docs/lignage.png` | Fait |
| P3 Exactitude et intégrité | Réconciliation automatique, empreintes SHA-256 | 2, 6 | `ingestion/landing/depot_landing.py` (SHA-256, manifestes), DQ-01 dans `ingestion/bronze/`, test `tests/test_dq01_alteration.py` ; sommes réconciliées RC-02 à RC-05 | Fait |
| P4 Exhaustivité | Contrôles de complétude à chaque couche | 3, 6 | DQ-03 dans `ingestion/bronze/` ; réconciliation RC-01 à RC-07 `dbt/credit_risk/models/controles/` ; test `tests/test_reconciliation.md` | Fait |
| P5 Actualité | Arrêté traité en moins de 2 heures, relançable à la demande | 7 | DQ-13 (`ingestion/api/banque_mondiale.py`) ; DQ-12 durée de traitement (`ingestion/controles/mesurer_delai.py`) ; alertes Telegram | Fait |
| P6 Adaptabilité | Modèle en étoile interrogeable, segmentation configurable | 5 | Modèle en étoile `dbt/credit_risk/models/marts/`, tranches de retard paramétrables (seed) | Fait |
| P7 Exactitude des rapports | Indicateurs du rapport rapprochés du gold | 1, 8 | `infra/terraform/postgres.tf` ; test `SET ROLE role_bi` : lecture de `marts` autorisée, `staging` refusé | En cours |
| P8 Exhaustivité des rapports | Encours, retards, défauts, concentration, migrations | 1, 8 | `infra/terraform/postgres.tf` ; test `SET ROLE role_bi` : lecture de `marts` autorisée, `staging` refusé | En cours |
| P9 Clarté et utilité | Définitions, date d'arrêté et score qualité visibles | 1, 8 | `infra/terraform/postgres.tf` ; test `SET ROLE role_bi` : lecture de `marts` autorisée, `staging` refusé | En cours |
| P10 Fréquence | Arrêté mensuel planifié, arrêté à la demande possible | 7 | DQ-13 (`ingestion/api/banque_mondiale.py`) ; DQ-12 durée de traitement (`ingestion/controles/mesurer_delai.py`) ; alertes Telegram | Fait |
| P11 Distribution | Rôles d'accès par profil, données sensibles masquées | 1, 8 | `infra/terraform/postgres.tf` ; test `SET ROLE role_bi` : lecture de `marts` autorisée, `staging` refusé | En cours |
| P12 à P14 Revue prudentielle | Hors périmètre ; piste d'audit conservée | 1, 6, 7 | `infra/postgres/01_ctl_tables.sql` ; score qualité `ctl.dq_score` ; `ingestion/controles/publier_controles.py` ; historique des exécutions Airflow ; `docs/exploitation.md` | Fait |