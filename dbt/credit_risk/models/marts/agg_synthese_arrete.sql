-- Une ligne par arrêté : les indicateurs de la page de synthèse.
select
    arrete,
    arrete_key,
    count(*)                                                    as nb_contrats,
    sum(encours)                                                as encours_total,
    sum(encours) filter (where jours_retard_significatif > 0)   as encours_en_retard,
    coalesce(sum(encours) filter (where est_defaut and encours_connu), 0) as encours_en_defaut_connu,   -- H14
    round(coalesce(sum(encours) filter (where est_defaut and encours_connu), 0)
          / nullif(sum(encours), 0), 6)                         as taux_creances_souffrance,
    count(*) filter (where est_defaut)                          as nb_contrats_defaut,
    count(*) filter (where est_defaut and not encours_connu)    as nb_defaut_encours_inconnu,   -- H14
    count(*) filter (where not encours_connu)                   as nb_encours_inconnu
from {{ ref('fct_exposition_mensuelle') }}
where est_en_portefeuille
group by arrete, arrete_key