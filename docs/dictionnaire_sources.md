
# Dictionnaire des sources

Inventaire des colonnes retenues pour chaque source, avec leur catégorie et leur usage dans la plateforme. Les colonnes non listées sont chargées en bronze mais non transformées.

| Version | Date | Modification |
| --- | --- | --- |
| 1.0 | 2026-10-04 | Création à partir de HomeCredit_columns_description.csv |

## application_train / application_test — Système d'octroi

- **Grain :** une demande de crédit en cours (un client)
- **Clé :** SK_ID_CURR
- **Non retenues :** statistiques logement (`*_AVG`, `*_MODE`, `*_MEDI`), `FLAG_DOCUMENT_*`

| Colonne | Catégorie | Signification | Usage |
| --- | --- | --- | --- |
| SK_ID_CURR | Clé | Identifiant de la demande / du client | Clé de toutes les jointures |
| TARGET | Catégorie | 1 = retard de plus de X jours sur l'une des Y premières échéances (X et Y non communiqués), 0 = sinon ; train uniquement | Cible du projet DS (différente du défaut H6) |
| NAME_CONTRACT_TYPE | Catégorie | Prêt cash ou crédit renouvelable | Segment |
| CODE_GENDER | Catégorie | Sexe | Donnée sensible, masquée (P11) |
| AMT_INCOME_TOTAL | Montant | Revenu annuel | Taux d'effort, tranche de revenu |
| AMT_CREDIT | Montant | Montant du crédit | Réconciliation RC-02, exposition |
| AMT_ANNUITY | Montant | Annuité de remboursement | Taux d'effort |
| AMT_GOODS_PRICE | Montant | Prix du bien financé (crédit à la consommation) | Feature DS |
| NAME_INCOME_TYPE | Catégorie | Type de revenu (salarié, retraité, entrepreneur…) | Vérification de H5 |
| NAME_EDUCATION_TYPE | Catégorie | Niveau d'études le plus élevé | Dimension client |
| NAME_FAMILY_STATUS | Catégorie | Situation familiale | Dimension client |
| CNT_CHILDREN | Compteur | Nombre d'enfants | Dimension client |
| DAYS_BIRTH | Date relative | Âge en jours au moment de la demande | Date de naissance (H1), tranche d'âge |
| DAYS_EMPLOYED | Date relative | Jours depuis le début de l'emploi actuel | Date d'embauche (H1, H5) |
| OCCUPATION_TYPE | Catégorie | Profession | Dimension client |
| REGION_RATING_CLIENT | Catégorie | Note de la région du client (1, 2, 3) | Feature DS |
| EXT_SOURCE_1, 2, 3 | Score | Scores externes normalisés | Features DS |
| AMT_REQ_CREDIT_BUREAU_* | Compteur | Nombre de consultations du bureau de crédit avant la demande | Features DS |

## bureau — Bureau de crédit externe

- **Grain :** un crédit du client déclaré par un autre établissement
- **Clés :** SK_ID_BUREAU (nommée SK_BUREAU_ID dans le dictionnaire, voir C1), SK_ID_CURR

| Colonne | Catégorie | Signification | Usage |
| --- | --- | --- | --- |
| SK_ID_BUREAU | Clé | Identifiant recodé du crédit externe | Jointure avec bureau_balance |
| SK_ID_CURR | Clé | Identifiant de la demande en cours | Jointure avec le client |
| CREDIT_ACTIVE | Catégorie | Statut du crédit (actif, clôturé…) | Nombre de crédits externes actifs |
| CREDIT_CURRENCY | Catégorie | Devise recodée du crédit | Filtre devise (H3) |
| CREDIT_TYPE | Catégorie | Type de crédit (auto, cash…) | Dimension, feature DS |
| DAYS_CREDIT | Date relative | Jours entre l'ouverture du crédit externe et la demande | Date d'ouverture (H1) |
| CREDIT_DAY_OVERDUE | Retard | Jours de retard au moment de la demande | Pire retard externe |
| AMT_CREDIT_SUM | Montant | Montant du crédit externe | Exposition externe |
| AMT_CREDIT_SUM_DEBT | Montant | Dette restante | Dette externe totale, feature DS |
| AMT_CREDIT_SUM_OVERDUE | Montant | Montant actuellement en retard | Feature DS |

## bureau_balance — Historique mensuel du bureau

- **Grain :** un crédit externe × un mois
- **Clé :** SK_ID_BUREAU + MONTHS_BALANCE

| Colonne | Catégorie | Signification | Usage |
| --- | --- | --- | --- |
| SK_ID_BUREAU | Clé | Identifiant du crédit externe | Jointure avec bureau |
| MONTHS_BALANCE | Date relative | Mois relatif à la demande (-1 = le plus récent) | Arrêté (H2) |
| STATUS | Catégorie | 0 = à jour, 1 = 1-30 j, 2 = 31-60 j, 3 = 61-90 j, 4 = 91-120 j, 5 = plus de 120 j ou cédé ou passé en perte, C = clôturé, X = inconnu | Historique de retard externe |

## previous_application — Historique d'octroi

- **Grain :** une demande passée (pas forcément devenue un crédit)
- **Clés :** SK_ID_PREV, SK_ID_CURR

| Colonne | Catégorie | Signification | Usage |
| --- | --- | --- | --- |
| SK_ID_PREV | Clé | Identifiant de la demande passée | Jointure avec les suivis mensuels et paiements |
| SK_ID_CURR | Clé | Identifiant de la demande en cours | Jointure avec le client |
| NAME_CONTRACT_TYPE | Catégorie | Type de produit (cash, consommation, renouvelable) | Segment |
| NAME_CONTRACT_STATUS | Catégorie | Approuvée, annulée, refusée, offre non utilisée | Filtre des contrats (H9), taux de refus |
| AMT_APPLICATION | Montant | Montant demandé | Feature DS |
| AMT_CREDIT | Montant | Montant finalement accordé | Contrats |
| AMT_ANNUITY | Montant | Annuité | Calcul de l'encours (H8) |
| CNT_PAYMENT | Compteur | Durée du crédit en nombre d'échéances | Dimension contrat |
| DAYS_DECISION | Date relative | Date de décision relative à la demande en cours | Date de décision (H1) |
| NAME_PORTFOLIO | Catégorie | Portefeuille : cash, point de vente, auto… | Segment de risque |
| FLAG_LAST_APPL_PER_CONTRACT | Indicateur | Dernière demande pour ce contrat | Dédoublonnage (H9) |
| NFLAG_LAST_APPL_IN_DAY | Indicateur | Dernière demande du jour | Dédoublonnage (H9) |

## POS_CASH_balance — Suivi mensuel des prêts

- **Grain :** un prêt × un mois
- **Clé :** SK_ID_PREV + MONTHS_BALANCE

| Colonne | Catégorie | Signification | Usage |
| --- | --- | --- | --- |
| SK_ID_PREV | Clé | Identifiant du prêt | Jointure avec previous_application |
| SK_ID_CURR | Clé | Identifiant de la demande en cours | Jointure avec le client |
| MONTHS_BALANCE | Date relative | Mois relatif à la demande (0 = au moment de la demande) | Arrêté (H2) |
| CNT_INSTALMENT | Compteur | Durée du prêt (peut changer) | Dimension contrat |
| CNT_INSTALMENT_FUTURE | Compteur | Échéances restant à payer | Encours (H8) |
| NAME_CONTRACT_STATUS | Catégorie | Statut du contrat dans le mois | Contrats actifs |
| SK_DPD | Retard | Jours de retard dans le mois | Tranches, défaut (H6) |
| SK_DPD_DEF | Retard | Jours de retard en ignorant les petites dettes | Défaut (choix H6) |

## credit_card_balance — Suivi mensuel des cartes

- **Grain :** une carte × un mois
- **Clé :** SK_ID_PREV + MONTHS_BALANCE

| Colonne | Catégorie | Signification | Usage |
| --- | --- | --- | --- |
| SK_ID_PREV | Clé | Identifiant de la carte | Jointure avec previous_application |
| SK_ID_CURR | Clé | Identifiant de la demande en cours | Jointure avec le client |
| MONTHS_BALANCE | Date relative | Mois relatif à la demande | Arrêté (H2) |
| AMT_BALANCE | Montant | Solde de la carte dans le mois | Encours (H8), réconciliation RC-03 |
| AMT_CREDIT_LIMIT_ACTUAL | Montant | Plafond de la carte | Taux d'utilisation |
| AMT_RECEIVABLE_PRINCIPAL | Montant | Capital restant à recevoir | Alternative à AMT_BALANCE pour H8 |
| AMT_PAYMENT_TOTAL_CURRENT | Montant | Total payé dans le mois | Feature DS |
| NAME_CONTRACT_STATUS | Catégorie | Statut du contrat | Contrats actifs |
| SK_DPD | Retard | Jours de retard dans le mois | Tranches, défaut (H6) |
| SK_DPD_DEF | Retard | Jours de retard avec tolérance | Défaut (choix H6) |

## installments_payments — Échéancier et paiements

- **Grain :** un paiement (une échéance peut avoir plusieurs paiements, voir C10)
- **Clé :** à déterminer au profilage

| Colonne | Catégorie | Signification | Usage |
| --- | --- | --- | --- |
| SK_ID_PREV | Clé | Identifiant du crédit | Jointure avec previous_application |
| SK_ID_CURR | Clé | Identifiant de la demande en cours | Jointure avec le client |
| NUM_INSTALMENT_VERSION | Compteur | Version du calendrier (0 = carte) | Détection des changements de calendrier |
| NUM_INSTALMENT_NUMBER | Compteur | Numéro de l'échéance | Suivi des échéances |
| DAYS_INSTALMENT | Date relative | Date prévue de l'échéance | Date prévue (H1), retard de paiement |
| DAYS_ENTRY_PAYMENT | Date relative | Date réelle du paiement | Date payée (H1), retard de paiement |
| AMT_INSTALMENT | Montant | Montant prévu | Écart dû / payé |
| AMT_PAYMENT | Montant | Montant réellement payé | Réconciliation RC-04 |

## Points d'attention relevés à la lecture

| N° | Constat | Traitement prévu | Statut |
| --- | --- | --- | --- |
| C1 | Nom de clé du bureau différent entre dictionnaire et fichiers | Vérification sur les fichiers | À vérifier (Lot 2) |
| C2 | Espaces en fin de certains noms de colonnes | Nettoyage des noms au chargement | À vérifier (Lot 2) |
| C3 | Dictionnaire encodé en Latin-1 (caractères illisibles) | Encodage précisé au chargement | Confirmé |
| C4 | Identifiants anonymisés (hashed, recoded) | Usage pour les jointures uniquement | Confirmé |
| C5 | TARGET différent du défaut à 90 jours | Note dans H6 | Confirmé |
| C6 | MONTHS_BALANCE = 0 souvent identique à -1 | Exclusion du mois 0 (H2) | À vérifier (Lot 2) |
| C7 | Plusieurs devises dans le bureau | Filtre devise (H3) | À vérifier (Lot 2) |
| C8 | Doublons de demandes passées | Dédoublonnage (H9) | À vérifier (Lot 2) |
| C9 | Demandes passées non transformées en crédit | Filtre Approved (H9) | Confirmé |
| C10 | Plusieurs paiements par échéance | Grain au niveau paiement | À vérifier (Lot 2) |
| C11 | Colonne AMT_RECIVABLE mal orthographiée | Renommage en silver | À vérifier (Lot 2) |
