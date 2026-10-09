# Registre des décisions techniques

## ADR-001 — Image Docker de MinIO

- **Date :** 2026-10-05
- **Contexte :** l'image officielle `minio/minio` n'est plus téléchargeable depuis Docker Hub (« pull access denied ») ni depuis Quay (« unauthorized »). MinIO est devenu une distribution source uniquement et a retiré ses images publiques.
- **Décision :** utiliser l'image communautaire `pgsty/minio:RELEASE.2026-08-04T00-00-00Z`, version fixée, avec un contrôle de santé basé sur `curl`.
- **Conséquences :** dépendance à un mainteneur tiers, à surveiller. Alternatives open source compatibles S3 si besoin : SeaweedFS, Garage.
## ADR-002 — Incrémental par arrêté entier pour les faits mensuels

- **Date :** 2026-10-09
- **Contexte :** avec `unique_key = 'cle'`, la stratégie `delete+insert` de dbt ne supprime que les lignes dont la clé est retraitée ; une ligne supprimée à la source restait dans le gold. Le test de réconciliation l'a révélé.
- **Décision :** `unique_key = 'arrete'` : chaque arrêté retraité est entièrement supprimé puis réinséré (écrasement de partition). Contrôle RC-07 ajouté entre intermediate et gold (défense en profondeur).
- **Conséquences :** les suppressions à la source se propagent ; un arrêté ancien modifié exige une reconstruction complète (`--full-refresh`).