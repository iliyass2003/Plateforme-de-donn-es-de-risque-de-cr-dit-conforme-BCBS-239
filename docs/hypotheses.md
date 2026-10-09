
# Registre des hypothèses

Ce registre liste toutes les règles adoptées lorsque les données ne fournissent pas directement une information. Chaque hypothèse est appliquée de façon unique et citée dans le code qui l'implémente.

| Version | Date | Modification |
| --- | --- | --- |
| 1.0 | 2026-10-04 | Création du registre (H1 à H8) |
| 1.1 | 2026-10-04 | Mise à jour après lecture du dictionnaire : H2, H3, H6, ajout de H9 |
| 1.2 | 2026-10-07 | Décisions après profilage (docs/profilage.md) : H2, H3, H5, H6, H9 validées ; ajout de H10 et H11 |

## H1 — Jour de référence T0

- **Énoncé :** toutes les demandes en cours sont datées au 31/12/2025 (T0). Les colonnes `DAYS_*` sont converties en dates : date = T0 + nombre de jours.
- **Justification :** les données ne fournissent que des écarts relatifs à la date de demande, qui n'est pas connue.
- **Limite :** dates et âges approximatifs, les demandes réelles étant étalées dans le temps.
- **Application :** couche silver, modèles de staging.
- **Statut :** validée.

## H2 — Arrêtés mensuels

- **Énoncé :** `MONTHS_BALANCE = -n` correspond à l'arrêté de fin de mois situé n mois avant T0 (-1 → 30/11/2025 ; -24 → 31/12/2023). Les 24 derniers arrêtés sont traités.
- **Justification :** reproduire un traitement mensuel réel avec les données existantes.
- **Limite :** l'historique antérieur à 24 mois n'est pas exploité. Le mois 0 (information au moment de la demande, souvent identique à -1) est exclu des arrêtés ; à confirmer au profilage.
- **Application :** zone landing (découpage par arrêté) et couche silver.
- **Statut :** validée.

## H3 — Devise

- **Énoncé :** tous les montants internes sont exprimés en MAD par convention.
- **Justification :** la devise n'est pas précisée dans le jeu de données.
- **Limite :** les crédits du bureau externe sont exprimés dans plusieurs devises recodées (`CREDIT_CURRENCY`). Seuls les montants dans la devise majoritaire sont agrégés ; les autres sont signalés. À confirmer au profilage.
- **Application :** documentation des colonnes de montant ; staging du bureau.
- **Statut :** validée pour les montants internes ; à vérifier pour le bureau (Lot 2).

## H4 — Marché de référence macroéconomique

- **Énoncé :** les indicateurs macroéconomiques utilisés sont ceux du Maroc (Banque mondiale).
- **Justification :** cohérence avec le contexte de la Banque Atlas.
- **Limite :** les clients du jeu de données ne sont pas marocains.
- **Application :** dimension macro (gold).
- **Statut :** validée.

## H5 — Valeur 365 243 dans DAYS_EMPLOYED

- **Énoncé :** la valeur 365 243 est remplacée par une valeur vide et l'indicateur `est_sans_emploi` est mis à vrai.
- **Justification :** 365 243 jours (1 000 ans) est un code technique, non une ancienneté réelle.
- **Limite :** à confirmer par croisement avec le type de revenu ; la même valeur peut apparaître dans des colonnes `DAYS_*` de previous_application.
- **Application :** couche silver, staging des demandes.
- **Statut :** à vérifier au profilage (Lot 2).

## H6 — Définition du défaut

- **Énoncé :** un contrat est en défaut lorsqu'il présente plus de 90 jours de retard.
- **Justification :** définition du défaut de la réglementation bâloise et seuil par défaut d'IFRS 9.
- **Limite :** choix entre `SK_DPD` et `SK_DPD_DEF` à arrêter après profilage.
- **Attention :** la variable `TARGET` du jeu de données n'est pas ce défaut. Elle signale un retard de plus de X jours sur l'une des Y premières échéances, X et Y n'étant pas communiqués. Les deux notions ne doivent jamais être confondues dans le reporting.
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
- **Limite :** les mensualités incluant des intérêts, l'encours des prêts est légèrement surestimé. Pour les cartes, `AMT_RECEIVABLE_PRINCIPAL` est une alternative à évaluer au profilage.
- **Application :** couche silver (`int_expositions_mensuelles`).
- **Statut :** validée.

## H9 — Demandes passées devenues contrats

- **Énoncé :** seules les demandes passées au statut « Approved » sont considérées comme des contrats. En cas de doublon, seule la dernière demande par contrat est conservée (`FLAG_LAST_APPL_PER_CONTRACT = 'Y'` et `NFLAG_LAST_APPL_IN_DAY = 1`).
- **Justification :** une demande peut être refusée, annulée ou non utilisée, et le dictionnaire signale des doublons de saisie.
- **Limite :** valeurs exactes des indicateurs à vérifier au profilage.
- **Application :** couche silver, staging des demandes passées.
- **Statut :** à vérifier au profilage (Lot 2).


## Décisions après profilage (version 1.2)

Source : `docs/profilage.md`, données complètes.

| Hypothèse | Résultat mesuré | Décision |
| --- | --- | --- |
| H2 | Historique jusqu'à 96 mois ; mois 0 présent uniquement dans bureau_balance (610 965 lignes) | Validée : 24 arrêtés, mois 0 exclu |
| H3 | currency 1 = 1 715 020 crédits sur 1 716 428 | Validée : agrégation de currency 1, autres devises signalées |
| H5 | 365243 : 55 352 retraités et 22 sans-emploi, aucun autre type de revenu | Validée |
| H6 | SK_DPD > 90 : 119 118 lignes ; SK_DPD_DEF > 90 : 4 682 lignes (POS) | Validée avec SK_DPD_DEF (obligation significative) |
| H9 | 9 261 demandes non marquées Y/1 sur 1 670 214 | Validée |

## H10 — Lignes orphelines des suivis mensuels et paiements

- **Énoncé :** les lignes de POS_CASH_balance, credit_card_balance et installments_payments dont le SK_ID_PREV est absent de previous_application sont conservées, rattachées au client par SK_ID_CURR, avec `contrat_connu = faux`. L'encours d'un prêt orphelin n'est pas calculé et est signalé.
- **Justification :** 3,4 % à 28 % des lignes selon la table ; les supprimer violerait l'exhaustivité (BCBS 239, P4).
- **Limite :** attributs du contrat inconnus pour ces lignes.
- **Application :** couche silver.
- **Statut :** validée.

## H11 — Historique bureau orphelin et grain des paiements

- **Énoncé :** les 3 120 184 lignes de bureau_balance sans crédit correspondant dans bureau sont exclues et comptées à chaque arrêté. Le grain d'installments_payments est le paiement (730 634 échéances ont plusieurs lignes) ; une clé technique est ajoutée en bronze.
- **Justification :** aucun lien possible vers un client ; pas de clé naturelle unique pour les paiements.
- **Application :** couches bronze et silver.
- **Statut :** validée.
## Note sur H4 — indicateur retiré

L'indicateur `FR.INR.LEND` (taux d'intérêt débiteur) n'est pas publié pour le Maroc par la Banque mondiale : 0 année disponible, contrôle DQ-13 en KO le 2026-10-09. Il est retiré de l'extraction. Indicateurs conservés : croissance du PIB réel, inflation, chômage (dernière année 2025).