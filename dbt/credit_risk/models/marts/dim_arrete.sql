-- Une ligne par arrêté mensuel présent dans les expositions.
select distinct
    arrete,
    cast(to_char(arrete, 'YYYYMMDD') as integer)    as arrete_key,
    extract(year from arrete)::int                  as annee,
    extract(quarter from arrete)::int               as trimestre,
    extract(month from arrete)::int                 as mois,
    to_char(arrete, 'YYYY-MM')                      as periode,
    (arrete = max(arrete) over ())                  as est_dernier_arrete
from {{ ref('int_expositions_mensuelles') }}