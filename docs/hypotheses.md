# Registre des hypothèses

Ce registre liste toutes les règles adoptées lorsque les données ne fournissent pas directement une information. Chaque hypothèse est appliquée de façon unique et citée dans le code qui l'implémente.

| Version | Date | Modification |
| --- | --- | --- |
| 1.0 | 2026-10-04 | Création du registre (H1 à H8) |

## H1 — Jour de référence T0

- **Énoncé :** toutes les demandes en cours sont datées au 31/12/2025 (T0). Les colonnes `DAYS_*` sont converties en dates : date = T0 + nombre de jours.
- **Justification :** les données ne fournissent que des écarts relatifs à la date de demande, qui n'est pas connue.
- **Limite :** dates et âges approximatifs, les demandes réelles étant étalées dans le temps.
- **Application :** couche silver, modèles de staging.
- **Statut :** validée.

## H2 — Arrêtés mensuels

- **Énoncé :** `MONTHS_BALANCE = -n` correspond à l'arrêté de fin de mois situé n mois avant T0 (-1 → 30/11/2025 ; -24 → 31/12/2023). Les 24 derniers arrêtés sont traités.
- **Justification :** reproduire un traitement mensuel réel avec les données existantes.
- **Limite :** l'historique antérieur à 24 mois n'est pas exploité.
- **Application :** zone landing (découpage par arrêté) et couche silver.
- **Statut :** validée.

## H3 — Devise

- **Énoncé :** tous les montants sont exprimés en MAD par convention.
- **Justification :** la devise n'est pas précisée dans le jeu de données.
- **Limite :** aucune.
- **Application :** documentation des colonnes de montant.
- **Statut :** validée.

## H4 — Marché de référence macroéconomique

- **Énoncé :** les indicateurs macroéconomiques utilisés sont ceux du Maroc (Banque mondiale).
- **Justification :** cohérence avec le contexte de la Banque Atlas.
- **Limite :** les clients du jeu de données ne sont pas marocains.
- **Application :** dimension macro (gold).
- **Statut :** validée.

## H5 — Valeur 365 243 dans DAYS_EMPLOYED

- **Énoncé :** la valeur 365 243 est remplacée par une valeur vide et l'indicateur `est_sans_emploi` est mis à vrai.
- **Justification :** 365 243 jours (1 000 ans) est un code technique, non une ancienneté réelle.
- **Limite :** à confirmer par croisement avec le type de revenu.
- **Application :** couche silver, staging des demandes.
- **Statut :** à vérifier au profilage (Lot 2).

## H6 — Définition du défaut

- **Énoncé :** un contrat est en défaut lorsqu'il présente plus de 90 jours de retard.
- **Justification :** définition du défaut de la réglementation bâloise et seuil par défaut d'IFRS 9.
- **Limite :** choix entre `SK_DPD` et `SK_DPD_DEF` à arrêter après profilage.
- **Application :** couche gold, table d'exposition mensuelle.
- **Statut :** à vérifier au profilage (Lot 2).

## H7 — Échantillon de développement

- **Énoncé :** en développement, 10 % des clients sont tirés au hasard (graine fixe) avec toutes leurs données liées.
- **Justification :** réduire le volume tout en conservant l'intégrité référentielle.
- **Limite :** les indicateurs calculés sur l'échantillon ne sont pas ceux du portefeuille complet.
- **Application :** script d'échantillonnage, environnement dev.
- **Statut :** validée.

## H8 — Calcul de l'encours

- **Énoncé :** encours d'une carte = `AMT_BALANCE` ; encours d'un prêt = `CNT_INSTALMENT_FUTURE` × `AMT_ANNUITY`.
- **Justification :** le capital restant dû des prêts n'est pas fourni.
- **Limite :** les mensualités incluant des intérêts, l'encours des prêts est légèrement surestimé.
- **Application :** couche silver (`int_expositions_mensuelles`).
- **Statut :** validée.