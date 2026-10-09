-- Une ligne par arrêté, segment et tranche de retard.
select
    f.arrete || '-' || f.segment || '-' || f.tranche_code       as cle,
    f.arrete,
    f.segment,
    f.tranche_code,
    t.tranche_libelle,
    count(*)                                                    as nb_contrats,
    sum(f.encours)                                              as encours,
    count(*) filter (where f.est_defaut)                        as nb_defaut,
    sum(f.encours) filter (where f.est_defaut)                  as encours_defaut,
    count(*) filter (where not f.encours_connu)                 as nb_encours_inconnu
from {{ ref('fct_exposition_mensuelle') }} f
join {{ ref('dim_tranche_retard') }} t on t.tranche_code = f.tranche_code
where f.est_en_portefeuille
group by f.arrete, f.segment, f.tranche_code, t.tranche_libelle