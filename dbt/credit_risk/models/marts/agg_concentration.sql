-- Part de l'encours (connu) détenue par les 20 plus gros clients, par arrêté.
with par_client as (
    select arrete, client_id, sum(encours) as encours
    from {{ ref('fct_exposition_mensuelle') }}
    where est_en_portefeuille and encours_connu
    group by arrete, client_id
),

classement as (
    select *, row_number() over (partition by arrete order by encours desc) as rang
    from par_client
)

select
    arrete,
    sum(encours)                                                as encours_total,
    sum(encours) filter (where rang <= 20)                      as encours_top_20,
    round(sum(encours) filter (where rang <= 20)
          / nullif(sum(encours), 0), 4)                         as taux_concentration_top_20
from classement
group by arrete