-- Une ligne par client : ses crédits dans les autres établissements.
-- H3 : devise principale seulement. H12 : trop-perçus exclus de la dette. H11 : historique orphelin exclu.
with credits as (
    select * from {{ ref('stg_homecredit__credits_externes') }}
    where est_devise_principale
),

pire_retard_12_mois as (
    -- Pire tranche de retard (1 à 5) sur les 12 derniers arrêtés ; jointure interne = orphelins exclus
    select c.client_id, max(cast(h.statut_mois as integer)) as pire_statut_12_mois
    from {{ ref('stg_homecredit__historique_externe') }} h
    join credits c on c.credit_externe_id = h.credit_externe_id
    where h.statut_mois in ('1', '2', '3', '4', '5')
      and h.arrete > date '{{ var("t0_date") }}' - interval '12 months'
    group by c.client_id
)

select
    c.client_id,
    count(*)                                                        as nb_credits_externes,
    count(*) filter (where c.statut_credit = 'Active')              as nb_credits_actifs,
    coalesce(sum(c.dette_restante) filter (
        where c.statut_credit = 'Active' and not c.est_trop_percu), 0) as dette_externe,
    coalesce(sum(c.montant_en_retard), 0)                           as montant_en_retard_externe,
    max(c.jours_retard)                                             as pire_retard_externe_jours,
    count(*) filter (where c.est_trop_percu)                        as nb_trop_percus,
    coalesce(max(r.pire_statut_12_mois), 0)                         as pire_statut_12_mois
from credits c
left join pire_retard_12_mois r on r.client_id = c.client_id
group by c.client_id