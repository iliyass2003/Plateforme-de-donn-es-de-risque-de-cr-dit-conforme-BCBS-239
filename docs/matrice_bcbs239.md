# Matrice de conformité BCBS 239

Correspondance entre les principes BCBS 239 (Comité de Bâle, 2013) et leur mise en œuvre dans la plateforme. La colonne « Preuve » est complétée au fil des lots.

| Version | Date | Modification |
| --- | --- | --- |
| 1.0 | 2026-10-04 | Création, preuves à compléter |

| Principe | Exigence dans le projet | Lot | Preuve | Statut |
| --- | --- | --- | --- | --- |
| P1 Gouvernance | Propriétaires désignés, politique qualité écrite | 0 | `docs/gouvernance.md` | Fait |
| P2 Architecture et infrastructure | Architecture en couches, dictionnaire unique, identifiants cohérents | 0, 5 | `docs/architecture.md`, `docs/dictionnaire_sources.md`, lignage dbt `docs/lignage.png` | Fait |
| P3 Exactitude et intégrité | Réconciliation automatique, empreintes SHA-256 | 2, 6 | `ingestion/landing/depot_landing.py` (SHA-256, manifestes), DQ-01 dans `ingestion/bronze/`, test `tests/test_dq01_alteration.py` | En cours |
| P4 Exhaustivité | Contrôles de complétude à chaque couche | 3, 6 | DQ-03 dans `ingestion/bronze/` (lignes chargées = manifeste) | En cours |
| P5 Actualité | Arrêté traité en moins de 2 heures, relançable à la demande | 7 | `ingestion/api/banque_mondiale.py` (DQ-13 dans ctl.control_results) | En cours |
| P6 Adaptabilité | Modèle en étoile interrogeable, segmentation configurable | 5 | Modèle en étoile `dbt/credit_risk/models/marts/`, tranches de retard paramétrables (seed) | Fait |
| P7 Exactitude des rapports | Indicateurs du rapport rapprochés du gold | 1, 8 | `infra/terraform/postgres.tf` ; test `SET ROLE role_bi` : lecture de `marts` autorisée, `staging` refusé | En cours |
| P8 Exhaustivité des rapports | Encours, retards, défauts, concentration, migrations | 1, 8 | `infra/terraform/postgres.tf` ; test `SET ROLE role_bi` : lecture de `marts` autorisée, `staging` refusé | En cours |
| P9 Clarté et utilité | Définitions, date d'arrêté et score qualité visibles | 1, 8 | `infra/terraform/postgres.tf` ; test `SET ROLE role_bi` : lecture de `marts` autorisée, `staging` refusé | En cours |
| P10 Fréquence | Arrêté mensuel planifié, arrêté à la demande possible | 7 | `ingestion/api/banque_mondiale.py` (DQ-13 dans ctl.control_results) | En cours |
| P11 Distribution | Rôles d'accès par profil, données sensibles masquées | 1, 8 | `infra/terraform/postgres.tf` ; test `SET ROLE role_bi` : lecture de `marts` autorisée, `staging` refusé | En cours |
| P12 à P14 Revue prudentielle | Hors périmètre ; piste d'audit conservée | 1, 6, 7 | `infra/postgres/01_ctl_tables.sql` | En cours |