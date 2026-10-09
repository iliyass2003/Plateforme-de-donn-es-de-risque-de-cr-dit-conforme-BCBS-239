-- Une ligne par contrat et par arrêté : encours, retard, tranche, défaut.
-- H8 : encours. H10 : contrats inconnus gardés. H6 : défaut sur retard significatif.

with prets as (
    select
        p.cle, p.contrat_id, p.client_id, p.arrete,
        'pret'                                          as type_suivi,
        p.statut_contrat,
        (c.contrat_id is not null)                      as contrat_connu,
        coalesce(c.segment, 'Prêt non identifié')       as segment,
        p.nb_echeances_restantes * c.mensualite         as encours,   -- vide si contrat inconnu (H10)
        cast(null as numeric)                           as plafond,
        p.jours_retard_brut,
        p.jours_retard_significatif
    from {{ ref('stg_homecredit__suivi_prets') }} p
    left join {{ ref('int_contrats') }} c on c.contrat_id = p.contrat_id
    where p.cle not in (select cle from {{ ref('int_quarantaine') }} where entite = 'suivi_prets')
),

cartes as (
    select
        k.cle, k.contrat_id, k.client_id, k.arrete,
        'carte'                                         as type_suivi,
        k.statut_contrat,
        (c.contrat_id is not null)                      as contrat_connu,
        'Carte renouvelable'                            as segment,
        k.solde                                         as encours,   -- H8 : encours carte = solde
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
    (e.statut_contrat = 'Active')               as est_actif,
    t.tranche_code,
    t.tranche_libelle                           as tranche_retard,
    (e.jours_retard_significatif > 90)          as est_defaut     -- H6
from expositions e
left join {{ ref('ref_tranches_retard') }} t
    on e.jours_retard_significatif between t.jours_min and t.jours_max