-- Matrice de migration : tranche du mois précédent -> tranche du mois courant, par contrat.
with portefeuille as (
    select contrat_id, arrete, tranche_code, encours
    from {{ ref('fct_exposition_mensuelle') }}
    where est_en_portefeuille
),

transitions as (
    select
        cur.arrete,
        prev.tranche_code       as tranche_depart,
        cur.tranche_code        as tranche_arrivee,
        cur.encours
    from portefeuille cur
    join portefeuille prev
      on prev.contrat_id = cur.contrat_id
     and prev.arrete = (date_trunc('month', cur.arrete) - interval '1 day')::date   -- arrêté précédent
)

select
    arrete || '-' || tranche_depart || '-' || tranche_arrivee   as cle,
    arrete,
    tranche_depart,
    tranche_arrivee,
    count(*)                                                    as nb_contrats,
    sum(encours)                                                as encours,
    round(count(*)::numeric
          / sum(count(*)) over (partition by arrete, tranche_depart), 4) as taux_migration
from transitions
group by arrete, tranche_depart, tranche_arrivee