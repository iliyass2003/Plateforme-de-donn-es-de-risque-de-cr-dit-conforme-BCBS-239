# Plateforme de données de risque de crédit — conforme BCBS 239

Plateforme qui agrège, contrôle et réconcilie chaque mois les données de risque de crédit d'une banque de détail, du fichier source jusqu'au reporting, avec une traçabilité complète de chaque chiffre.

> **Statut :** en cours de réalisation — Lot 0 (cadrage et socle)

## Contexte

La **Banque Atlas** (fictive) distribue des crédits à la consommation : prêts cash, crédits au point de vente et cartes de crédit. Ses données de risque sont dispersées entre plusieurs systèmes (octroi, monétique, échéancier, bureau de crédit) et le reporting mensuel est produit à la main.

Ce projet construit la plateforme qui automatise ce reporting en respectant les principes **BCBS 239** du Comité de Bâle sur l'agrégation des données de risque.

Les données sont **réelles et anonymisées** : jeu *Home Credit Default Risk* (Kaggle) et indicateurs macroéconomiques du Maroc publiés par la Banque mondiale.

## Ce que démontre le projet

Pour chaque chiffre du reporting de risque, la plateforme permet de répondre à quatre questions :

| Question | Réponse technique |
| --- | --- |
| D'où vient-il ? | Lignage de la source au rapport |
| Est-il complet ? | Contrôles de complétude à chaque couche |
| Est-il juste ? | Réconciliation automatique source ↔ bronze ↔ gold |
| Quand a-t-il été produit ? | Journal des traitements par arrêté mensuel |

## Architecture (cible)

Sources → **Landing** (copie exacte) → **Bronze** (chargé tel quel) → **Silver** (nettoyé) → **Gold** (modèle en étoile) → Reporting, avec une couche de **contrôle** transverse.

Le schéma détaillé sera ajouté à la fin du Lot 0.

## Stack technique (100 % gratuite)

| Fonction | Outil |
| --- | --- |
| Conteneurs | Docker, Docker Compose |
| Stockage landing | MinIO |
| Warehouse | PostgreSQL |
| Transformation et tests | dbt Core |
| Qualité | dbt tests, Soda Core |
| Orchestration | Apache Airflow |
| Infrastructure as code | Terraform |
| CI/CD | GitHub Actions |
| Reporting | Power BI Desktop |

## Données

Les données ne sont pas incluses dans ce dépôt (volume et conditions d'utilisation de Kaggle). Un script de téléchargement sera fourni au Lot 1.

## Avancement

| Lot | Contenu | Statut |
| --- | --- | --- |
| 0 | Cadrage et socle | En cours |
| 1 | Infrastructure locale | À faire |
| 2 | Zone landing | Terminé |
| 3 | Zone bronze | Terminé |
| 4 | Zone silver | En cours |
| 5 | Zone gold | À faire |
| 6 | Contrôles et réconciliation | À faire |
| 7 | Orchestration | À faire |
| 8 | Sécurité, CI/CD et reporting | À faire |

## Auteur

meliani iliyass — [LinkedIn](https://www.linkedin.com/in/meliani-ilyass)


<!-- lot 0 :
github
le registre des hypothèses:Les données réelles ne contiennent jamais tout ce dont on a besoin. Quand il manque une information, on choisit une règle, on l'écrit, on la justifie, et on l'applique partout de la même façon. Ce choix écrit s'appelle une hypothèse.
identifiant, énoncé, justification, limite, où elle s'applique, statut (« validée » ou « à vérifier au profilage »). -->