# Dossier de modèle : PD et ECL IFRS 9

Statut : en construction. Chaque section est complétée au lot indiqué.

## 1. Objet du modèle
Probabilité de défaut à 12 mois par client, utilisée pour l'ECL IFRS 9. Propriétaire : équipe Data Science, Direction des Risques.

## 2. Données

**Source** : `marts.mart_features_client` (contrat vérifié à chaque lecture). Entraînement : 30 740 clients, test : 4 886 (échantillon de 10 %). Notebook : `ds/notebooks/01_exploration.ipynb`.

**Cible** : 7,94 % de clients en difficulté (cash : 8,20 %, renouvelables : 5,41 %). Cible déséquilibrée : modèle jugé sur l'AUC, le Gini et le KS.

**Manquants** : cartes 72 à 75 % (pas de carte), score externe 1 : 56 %. Les manques portent du signal (retraités : 5,5 % de difficultés ; sans crédit ailleurs : 9,8 %) : traités comme une classe à part, jamais imputés par la moyenne.

**Liens avec le risque** : scores externes 2 et 3 très séparateurs et monotones (de 18-20 % à 3 %) ; âge et retards passés monotones ; ancienneté en bosse ; taux d'effort faible (biais de sélection : seuls les crédits accordés sont observés).

**Corrélations** : montant / prix du bien (0,99), dette externe / ratio (0,83), annuité / montant (0,77), crédits / crédits actifs (0,74).

**Stabilité train / test** : population test d'une autre période : 0,9 % de renouvelables contre 9,4 % (PSI 0,21), prêts cash plus courts (16 mois contre 21) et plus petits (PSI 0,13), score externe 1 plus souvent renseigné (42 % de manquants contre 56 %), petits retards externes plus fréquents (15 % contre 4 %, PSI 0,16). Limite : la validation aléatoire (M7) peut être optimiste.

**Pouvoir prédictif (IV)** : aucune variable suspecte ; fortes : scores externes 2 et 3 ; moyennes : score externe 1, ancienneté, prix du bien ; nulles : taux d'effort, ratio de dette, type de contrat, entre autres. Environ 15 variables candidates pour la scorecard.

## 3. Hypothèses
Voir `docs/hypotheses_modele.md`. Résultats de sensibilité : à compléter (DS-6).

## 4. Méthodologie

1. **Découpage** : 70 % apprentissage (21 518 clients) / 30 % validation (9 222), stratifié, graine 42 (M7). Taux de la cible identique : 7,94 %.
2. **Variables créées** : `duree_mois` = montant ÷ mensualité (IV 0,146, 3e variable), `ratio_financement` = montant ÷ prix du bien.
3. **Classes et WoE** (optbinning) appris sur l'apprentissage seulement, relation monotone imposée ; WoE = ln(part des bons ÷ part des mauvais). Les manquants reçoivent le WoE empirique de leur classe (`metric_missing="empirical"`) : le réglage par défaut leur donnait 0 et effaçait leur signal (retraités : WoE +0,36).
4. **Sélection** (algorithme glouton) : IV ≥ 0,02 ; corrélation entre WoE ≤ 0,70. Écartées : `pct_paiements_en_retard` (corrélée à 0,87 avec `retard_paiement_max`), `montant_credit` (0,82 avec `prix_bien`), `annuite` (IV 0,019).
5. **Régression logistique** sur les WoE (statsmodels), élimination descendante, une variable à la fois : `age` retiré (coefficient positif, p = 0,47), puis `revenu_annuel` (p = 0,49). 14 variables, tous les coefficients négatifs et significatifs ; ordonnée −2,452 = ln(7,94 ÷ 92,06).
6. **Mise à l'échelle** : 600 points pour une cote de 50, PDO 20 ; facteur 28,85, offset 487,1 ; ordonnée et offset répartis également entre les variables.

Trace complète : run MLflow `scorecard_v1` (expérience `pd_scorecard`), notebook `ds/notebooks/02_scorecard.ipynb`.

## 5. Grille de score

Grille complète : `docs/grille_score_v1.csv` (variable, classe, clients, taux de difficulté, WoE, points). Score de la validation : de 469 (PD ≈ 65 %) à 671 (PD ≈ 0,17 %), moyenne 570,5. Exemple : `score_externe_2` rapporte de 15 points (score < 0,13 ; 21,1 % de difficultés) à 70 points (≥ 0,74 ; 2,2 %).

Limite : la classe « Missing » de `score_externe_2` ne compte que 47 clients (taux non fiable, ± 6 points) ; piste : WoE neutre pour les classes de moins de 1 % des clients.

## 6. Performances

| Critère | Seuil | Résultat | Statut |
| --- | --- | --- | --- |
| V1 AUC de validation | ≥ 0,70 | 0,739 (Gini 0,478) | Respecté |
| V2 KS de validation | ≥ 0,30 | 0,364 | Respecté |
| V3 Écart d'AUC apprentissage / validation | ≤ 0,03 | 0,024 | Respecté |
| V4 Écart-type de l'AUC sur 5 plis | ≤ 0,02 | 0,010 (moyenne 0,751) | Respecté |
| V9 Signes des coefficients | Tous négatifs | Oui, et dans chacun des 5 plis | Respecté |
| V5 à V8 | | À évaluer (DS-5) | |
| V10 | | À évaluer (DS-4) | |

## 7. Challenger
À compléter (DS-4).

## 8. Équité

Le sexe n'est pas une variable du modèle (M9) et n'est pas disponible dans la table de features. L'âge, lié au risque seul (de 11 % à 5 % de difficultés), n'apporte plus d'information une fois les autres variables connues : coefficient positif et non significatif (p = 0,47), retiré par l'élimination descendante. La scorecard n'utilise donc aucune donnée d'âge ni de sexe.

## 9. ECL
À compléter (DS-6) : méthode, exemple chiffré, résultats, contrôles E1 à E5.

## 10. Limites et suivi
À compléter (DS-7) : indicateurs de dérive DS-01 à DS-03.