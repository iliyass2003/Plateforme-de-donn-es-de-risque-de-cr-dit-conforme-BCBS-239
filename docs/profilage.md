# Rapport de profilage des sources

Source analysée : `data/source`

## 1. Volumes et en-têtes (C2)

Nombre de lignes et de colonnes ; noms de colonnes contenant des espaces.

| table                     |   lignes |   colonnes | noms_avec_espaces   |
|:--------------------------|---------:|-----------:|:--------------------|
| application_train.csv     |   307511 |        122 | aucun               |
| application_test.csv      |    48744 |        121 | aucun               |
| bureau.csv                |  1716428 |         17 | aucun               |
| bureau_balance.csv        | 27299925 |          3 | aucun               |
| previous_application.csv  |  1670214 |         37 | aucun               |
| POS_CASH_balance.csv      | 10001358 |          8 | aucun               |
| credit_card_balance.csv   |  3840312 |         23 | aucun               |
| installments_payments.csv | 13605401 |          8 | aucun               |

## 2. Unicité des clés

Une clé est unique si lignes = distincts.

| cle                             |   lignes |   distincts |
|:--------------------------------|---------:|------------:|
| application_train.SK_ID_CURR    |   307511 |      307511 |
| bureau.SK_ID_BUREAU             |  1716428 |     1716428 |
| previous_application.SK_ID_PREV |  1670214 |     1670214 |

## 3. Lignes orphelines

Nombre de lignes dont la clé n'existe pas dans la table parente.

| relation                             |   orphelins |
|:-------------------------------------|------------:|
| pos_cash -> previous_application     |      340561 |
| credit_card -> previous_application  |     1082816 |
| installments -> previous_application |     1250826 |
| bureau_balance -> bureau             |     3120184 |

## 4. Valeur 365243 dans DAYS_EMPLOYED (H5)

Si la valeur ne concerne que les retraités et les sans-emploi, H5 est confirmée.

| NAME_INCOME_TYPE     |   clients |   valeur_365243 |
|:---------------------|----------:|----------------:|
| Pensioner            |     55362 |           55352 |
| Unemployed           |        22 |              22 |
| Commercial associate |     71617 |               0 |
| Working              |    158774 |               0 |
| Businessman          |        10 |               0 |
| Student              |        18 |               0 |
| Maternity leave      |         5 |               0 |
| State servant        |     21703 |               0 |

## 5. Retards de plus de 90 jours (H6)

Écart entre retard brut (SK_DPD) et retard avec tolérance des petites dettes (SK_DPD_DEF).

| table_              |   dpd_plus_90 |   dpd_def_plus_90 |
|:--------------------|--------------:|------------------:|
| POS_CASH_balance    |        119118 |              4682 |
| credit_card_balance |         48226 |              1074 |

## 6. Profondeur des mois (H2, C6)

Jusqu'où remonte l'historique, et le mois 0 existe-t-il ?

| table_              |   mois_min |   mois_max |   lignes_mois_0 |
|:--------------------|-----------:|-----------:|----------------:|
| bureau_balance      |        -96 |          0 |          610965 |
| POS_CASH_balance    |        -96 |         -1 |               0 |
| credit_card_balance |        -96 |         -1 |               0 |

## 7. Devises du bureau (H3, C7)

Si une devise domine largement, H3 (filtre sur la devise majoritaire) est applicable.

| CREDIT_CURRENCY   |   credits |
|:------------------|----------:|
| currency 1        |   1715020 |
| currency 2        |      1224 |
| currency 3        |       174 |
| currency 4        |        10 |

## 8. Doublons de demandes passées (C8, H9)

Les demandes marquées N ou 0 sont les doublons signalés par le dictionnaire.

| FLAG_LAST_APPL_PER_CONTRACT   |   NFLAG_LAST_APPL_IN_DAY |   demandes |
|:------------------------------|-------------------------:|-----------:|
| Y                             |                        1 |    1660953 |
| N                             |                        0 |       5114 |
| N                             |                        1 |       3361 |
| Y                             |                        0 |        786 |

## 9. Plusieurs lignes par échéance (C10)

Si des échéances ont plusieurs lignes, le grain de la table est le paiement, pas l'échéance.

|   echeances |   echeances_multi_lignes |
|------------:|-------------------------:|
|    12861994 |                   730634 |
