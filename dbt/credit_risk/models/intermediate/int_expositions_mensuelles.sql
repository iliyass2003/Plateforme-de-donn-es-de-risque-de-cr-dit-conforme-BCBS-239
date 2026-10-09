-- Une ligne par contrat et par arrêté : encours, retard, tranche, défaut.
-- H8 : encours. H10 : contrats inconnus gardés. H6 : défaut sur retard significatif.
-- H13 : prêt en exigibilité anticipée -> dernier encours positif connu.

with prets_base as (
    select
        p.cle, p.contrat_id, p.client_id, p.arrete,
        p.statut_contrat,
        (c.contrat_id is not null)                      as contrat_connu,
        coalesce(c.segment, 'Prêt non identifié')       as segment,
        p.nb_echeances_restantes * c.mensualite         as encours_echeancier,   -- H8
        p.jours_retard_brut,
        p.jours_retard_significatif
    from {{ ref('stg_homecredit__suivi_prets') }} p
    left join {{ ref('int_contrats') }} c on c.contrat_id = p.contrat_id
    where p.cle not in (select cle from {{ ref('int_quarantaine') }} where entite = 'suivi_prets')
),

prets_reference as (
    -- arrêté du dernier encours positif connu, jusqu'à l'arrêté courant inclus
    select *,
        max(case when encours_echeancier > 0 then arrete end)
            over (partition by contrat_id order by arrete
                  rows between unbounded preceding and current row) as arrete_reference
    from prets_base
),

prets as (
    select
        p.cle, p.contrat_id, p.client_id, p.arrete,
        'pret'                                          as type_suivi,
        p.statut_contrat, p.contrat_connu, p.segment,
        case when p.statut_contrat in ('Demand', 'Amortized debt')
                  and coalesce(p.encours_echeancier, 0) = 0
             then r.encours_echeancier                  -- H13
             else p.encours_echeancier
        end                                             as encours,
        (p.statut_contrat in ('Demand', 'Amortized debt')
         and coalesce(p.encours_echeancier, 0) = 0)     as encours_reporte,
        cast(null as numeric)                           as plafond,
        p.jours_retard_brut,
        p.jours_retard_significatif
    from prets_reference p
    left join prets_base r
        on r.contrat_id = p.contrat_id and r.arrete = p.arrete_reference
),

cartes as (
    select
        k.cle, k.contrat_id, k.client_id, k.arrete,
        'carte'                                         as type_suivi,
        k.statut_contrat,
        (c.contrat_id is not null)                      as contrat_connu,
        'Carte renouvelable'                            as segment,
        k.solde                                         as encours,   -- H8
        false                                           as encours_reporte,
        k.plafond,
        k.jours_retard_brut,
        k.jours_retard_significatif
    from {{ ref('stg_homecredit__suivi_cartes') }} k
    left join {{ ref('int_contrats') }} c on c.contrat_id = k.contrat_id
    where k.cle not in (select cle from {{ ref('int_quarantaine') }} where entite = 'suivi_cartes')
),

expositions as (
    select * from prets
    union all
    select * from cartes
)

select
    e.*,
    (e.statut_contrat not in ('Completed', 'Returned to the store')) as est_en_portefeuille,
    t.tranche_code,
    t.tranche_libelle                                   as tranche_retard,
    (e.jours_retard_significatif > 90)                  as est_defaut,    -- H6
    (e.encours is not null)                             as encours_connu  -- H14 : limite signalée, jamais remplacée par 0
from expositions e
left join {{ ref('ref_tranches_retard') }} t
    on e.jours_retard_significatif between t.jours_min and t.jours_max