# Registre des hypothèses de modélisation (moteur ECL IFRS 9)

Version 1.0. Valeurs dans `ds/config_hypotheses.yaml`. Les hypothèses H1 à H15 de la plateforme restent valables (`docs/hypotheses.md`).

| N° | Hypothèse | Justification | Sensibilité testée |
| --- | --- | --- | --- |
| M1 | `defaut_observe` sert de cible pour la PD à 12 mois | Seule cible disponible ; difficultés de paiement sur les premières échéances, différente du défaut à 90 jours (H6) | Écart documenté avec H6 |
| M2 | Une PD par client, appliquée à tous ses contrats | Variables connues par client, à T0 | — |
| M3 | LGD = 45 % | Référence de Bâle pour les créances non garanties de premier rang ; aucune donnée de recouvrement | 35 % et 55 % |
| M4 | EAD prêt = encours ; EAD carte = solde + 50 % × (plafond − solde) | Une carte peut encore être tirée avant le défaut (CCF) | CCF de 30 % et 75 % |
| M5 | PD durée de vie = 1 − (1 − PD 12 mois)^T ; T = durée restante en années (prêts), 3 ans (cartes) | Risque annuel supposé constant ; durée de vie comportementale des cartes | T cartes de 2 et 5 ans |
| M6 | Scénarios central 60 %, défavorable 25 %, favorable 15 % ; PD × 1,00 / 1,25 / 0,90 | Aucun historique de défaut daté : ajustement expert | Multiplicateur défavorable 1,50 |
| M7 | Découpage stratifié 70 / 30, graine 42 ; validation croisée à 5 plis | Pas de dates réelles (H1) : pas de validation dans le temps | Stabilité entre plis |
| M8 | Stage 3 si défaut ; stage 2 si retard significatif > 30 jours ou PD 12 mois > 20 % ; sinon stage 1 | Une seule PD disponible (M2) : seuil absolu au lieu d'une comparaison à l'octroi | Seuil de PD 15 % et 30 % |
| M9 | Le sexe n'est jamais une variable du modèle | Non-discrimination ; minimisation (loi 09-08) | — |

**Règle** : une hypothèse qui change l'ECL totale de plus de 20 % est signalée comme hypothèse sensible.