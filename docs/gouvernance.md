# Gouvernance des données de risque

Ce document définit les responsabilités sur les données de risque de crédit de la Banque Atlas (principe BCBS 239 n° 1) et la politique de qualité appliquée par la plateforme. Les rôles métier sont fictifs.

| Version | Date | Modification |
| --- | --- | --- |
| 1.0 | 2026-10-04 | Création |

## 1. Rôles

| Rôle | Responsabilité |
| --- | --- |
| Propriétaire (data owner) | Définit les règles et définitions de son domaine, valide la qualité, arbitre les anomalies |
| Gestionnaire (data steward) | Suit la qualité au quotidien, analyse les rejets en quarantaine, alerte le propriétaire |
| Dépositaire (data custodian) | Équipe Data Engineering : stockage, traitements, contrôles automatiques, sécurité |

## 2. Domaines de données

| Domaine | Sources | Propriétaire | Gestionnaire |
| --- | --- | --- | --- |
| Octroi | application_train, application_test, previous_application | Directeur Crédit aux particuliers | Analyste octroi |
| Prêts | POS_CASH_balance | Directeur Crédit aux particuliers | Analyste portefeuille |
| Monétique | credit_card_balance | Responsable Monétique | Analyste monétique |
| Recouvrement | installments_payments | Responsable Recouvrement | Analyste recouvrement |
| Bureau externe | bureau, bureau_balance | Directeur des Risques | Analyste risque |
| Macroéconomie | API Banque mondiale | Directeur des Risques | Économiste |
| Reporting de risque | Couche gold | Directeur des Risques | Analyste risque |

Dépositaire de tous les domaines : équipe Data Engineering.

## 3. Politique qualité

### 3.1 Dimensions mesurées

| Dimension | Question | Exemple de contrôle |
| --- | --- | --- |
| Exactitude | La donnée est-elle juste ? | Montants non négatifs, réconciliation des sommes |
| Complétude | Manque-t-il des données ? | Nombre de lignes source = cible + rejets |
| Actualité | La donnée est-elle à jour ? | Arrêté traité en moins de 2 heures |
| Cohérence | Les données concordent-elles entre elles ? | Chaque contrat pointe vers un client connu |

### 3.2 Gravité des contrôles

- **Bloquant** : l'arrêté n'est pas publié ; le dépositaire est alerté immédiatement et informe le propriétaire du domaine.
- **Avertissement** : l'arrêté est publié ; l'anomalie est signalée au gestionnaire pour analyse.

### 3.3 Règle de publication d'un arrêté

Un arrêté est publié si et seulement si aucun contrôle bloquant n'est en échec. Le score qualité de l'arrêté est affiché sur chaque page du reporting. Objectif : score qualité supérieur ou égal à 98 %.

### 3.4 Traitement des rejets

Toute ligne rejetée est placée en quarantaine avec son motif. Le gestionnaire du domaine analyse les rejets à chaque arrêté. Aucune ligne n'est supprimée sans trace.

### 3.5 Hypothèses

Toute règle adoptée en l'absence d'information est inscrite au registre des hypothèses (`docs/hypotheses.md`) et validée par le propriétaire du domaine concerné.