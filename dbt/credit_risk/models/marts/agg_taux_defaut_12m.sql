-- Taux de défaut à 12 mois : part des contrats sains à l'arrêté M
-- qui tombent en défaut entre M (exclu) et M + 12 mois (inclus).
-- Calculé seulement quand les 12 mois suivants sont disponibles.
with portefeuille as (
    select contrat_id, arrete, est_defaut
    from {{ ref('fct_exposition_mensuelle') }}
    where est_en_portefeuille
),

sains as (
    select contrat_id, arrete
    from portefeuille
    where not est_defaut
      and arrete <= (select max(arrete) from portefeuille) - interval '12 months'
),

suivi as (
    select s.arrete, s.contrat_id, coalesce(bool_or(p.est_defaut), false) as defaut_12m
    from sains s
    left join portefeuille p
      on p.contrat_id = s.contrat_id
     and p.arrete > s.arrete
     and p.arrete <= s.arrete + interval '12 months'
    group by s.arrete, s.contrat_id
)

select
    arrete,
    count(*)                                        as nb_contrats_sains,
    count(*) filter (where defaut_12m)              as nb_defaut_12m,
    round(count(*) filter (where defaut_12m)::numeric / count(*), 6) as taux_defaut_12m
from suivi
group by arrete