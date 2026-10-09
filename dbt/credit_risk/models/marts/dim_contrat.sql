-- Une ligne par contrat : contrats connus (H9) et orphelins des suivis (H10).
with connus as (
    select contrat_id, client_id, segment, montant_accorde, mensualite,
           nb_echeances, date_decision, true as contrat_connu
    from {{ ref('int_contrats') }}
),

orphelins as (
    select distinct on (contrat_id)
           contrat_id, client_id, segment,
           cast(null as numeric) as montant_accorde, cast(null as numeric) as mensualite,
           cast(null as integer) as nb_echeances, cast(null as date) as date_decision,
           false as contrat_connu
    from {{ ref('int_expositions_mensuelles') }}
    where not contrat_connu
    order by contrat_id, arrete
)

select * from connus
union all
select * from orphelins