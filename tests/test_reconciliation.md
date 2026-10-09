# Test de blocage de la réconciliation

**Date :** 2026-10-09

## Procédure

1. Suppression de 10 lignes de `bronze.pos_cash_balance` pour l'arrêté du 2025-11-30.
2. Reconstruction dbt, puis `python ingestion/controles/publier_controles.py`.
3. Réparation : `python ingestion/bronze/chargement_bronze.py`, reconstruction dbt, republication.

## Premier essai : défaut découvert

La publication a réussi alors que 10 lignes manquaient. Cause : la table `fct_exposition_mensuelle` était incrémentale avec `unique_key = 'cle'` ; la stratégie `delete+insert` ne supprime que les clés reçues, donc des lignes supprimées à la source restaient dans le gold (suppressions physiques non propagées). Voir ADR-002.

## Second essai, après correction

- Incrémental par arrêté entier (`unique_key = 'arrete'`) : 15 795 lignes réinsérées au lieu de 15 805.
- RC-06 en KO pour le 2025-11-30, lot en ECHEC : « 1 contrôle(s) bloquant(s) en KO : publication refusée ».
- Après réparation : lot publié, score global 98,91 %.

Trace conservée dans `ctl.control_results` et `ctl.batch_log`.