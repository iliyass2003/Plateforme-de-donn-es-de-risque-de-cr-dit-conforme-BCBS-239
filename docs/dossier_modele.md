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
À compléter (DS-3, DS-5).

## 5. Grille de score
À compléter (DS-3).

## 6. Performances
À compléter (DS-3 à DS-5) : seuils V1 à V10.

## 7. Challenger
À compléter (DS-4).

## 8. Équité
Sexe exclu (M9). Effet de l'âge : à compléter (DS-3).

## 9. ECL
À compléter (DS-6) : méthode, exemple chiffré, résultats, contrôles E1 à E5.

## 10. Limites et suivi
À compléter (DS-7) : indicateurs de dérive DS-01 à DS-03.