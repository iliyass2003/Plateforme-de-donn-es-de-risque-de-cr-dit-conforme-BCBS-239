# Registre des décisions techniques

## ADR-001 — Image Docker de MinIO

- **Date :** 2026-10-05
- **Contexte :** l'image officielle `minio/minio` n'est plus téléchargeable depuis Docker Hub (« pull access denied ») ni depuis Quay (« unauthorized »). MinIO est devenu une distribution source uniquement et a retiré ses images publiques.
- **Décision :** utiliser l'image communautaire `pgsty/minio:RELEASE.2026-08-04T00-00-00Z`, version fixée, avec un contrôle de santé basé sur `curl`.
- **Conséquences :** dépendance à un mainteneur tiers, à surveiller. Alternatives open source compatibles S3 si besoin : SeaweedFS, Garage.