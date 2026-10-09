-- Une ligne par client : variables connues avant T0 pour le projet Data Science (IFRS 9).
-- Contrat d'interface : colonnes et types figés (voir mart_features_client.yml).

with passees as (
    select client_id,
           count(*)                                                        as nb_demandes,
           avg(case when statut_demande = 'Refused' then 1.0 else 0 end)   as taux_refus
    from {{ ref('stg_homecredit__demandes_passees') }}
    group by client_id
),

paiements as (
    select client_id,
           count(*)                                    as nb_paiements,
           avg(paye_en_retard::int)                    as pct_en_retard,
           max(jours_retard_paiement)                  as retard_max,
           count(*) filter (where non_paye)            as nb_non_payes
    from {{ ref('int_paiements_enrichis') }}
    group by client_id
),

cartes as (
    select client_id,
           avg(solde / nullif(plafond, 0))             as utilisation_moyenne,
           max(jours_retard_significatif)              as retard_max
    from {{ ref('stg_homecredit__suivi_cartes') }}
    group by client_id
)

select
    cast(d.client_id as bigint)                                             as client_id,
    cast(d.origine as text)                                                 as origine,
    cast(d.defaut_observe as integer)                                       as defaut_observe,
    cast(d.type_contrat as text)                                            as type_contrat,
    cast(d.montant_credit as numeric)                                       as montant_credit,
    cast(d.annuite as numeric)                                              as annuite,
    cast(d.revenu_annuel as numeric)                                        as revenu_annuel,
    cast(d.prix_bien as numeric)                                            as prix_bien,
    cast(d.annuite / nullif(d.revenu_annuel, 0) as numeric)                 as taux_effort,
    cast(extract(year from age(date '{{ var("t0_date") }}', d.date_naissance)) as integer) as age,
    cast(d.nb_enfants as integer)                                           as nb_enfants,
    cast(d.niveau_etudes as text)                                           as niveau_etudes,
    cast(d.type_revenu as text)                                             as type_revenu,
    cast(d.est_sans_emploi as boolean)                                      as est_sans_emploi,
    cast((date '{{ var("t0_date") }}' - d.date_embauche) / 365.25 as numeric) as anciennete_emploi_annees,
    cast(d.note_region as integer)                                          as note_region,
    cast(d.score_externe_1 as numeric)                                      as score_externe_1,
    cast(d.score_externe_2 as numeric)                                      as score_externe_2,
    cast(d.score_externe_3 as numeric)                                      as score_externe_3,
    cast(coalesce(b.nb_credits_externes, 0) as integer)                     as nb_credits_externes,
    cast(coalesce(b.nb_credits_actifs, 0) as integer)                       as nb_credits_externes_actifs,
    cast(coalesce(b.dette_externe, 0) as numeric)                           as dette_externe,
    cast(coalesce(b.dette_externe, 0) / nullif(d.revenu_annuel, 0) as numeric) as ratio_dette_externe_revenu,
    cast(b.pire_retard_externe_jours as integer)                            as pire_retard_externe_jours,
    cast(coalesce(b.pire_statut_12_mois, 0) as integer)                     as pire_statut_externe_12m,
    cast(coalesce(p.nb_demandes, 0) as integer)                             as nb_demandes_passees,
    cast(p.taux_refus as numeric)                                           as taux_refus_passe,
    cast(coalesce(pa.nb_paiements, 0) as integer)                           as nb_paiements,
    cast(pa.pct_en_retard as numeric)                                       as pct_paiements_en_retard,
    cast(pa.retard_max as integer)                                          as retard_paiement_max,
    cast(coalesce(pa.nb_non_payes, 0) as integer)                           as nb_echeances_non_payees,
    cast(k.utilisation_moyenne as numeric)                                  as utilisation_carte_moyenne,
    cast(k.retard_max as integer)                                           as retard_carte_max
from {{ ref('stg_homecredit__demandes') }} d
left join {{ ref('int_bureau_resume_client') }} b  on b.client_id = d.client_id
left join passees  p  on p.client_id  = d.client_id
left join paiements pa on pa.client_id = d.client_id
left join cartes   k  on k.client_id  = d.client_id